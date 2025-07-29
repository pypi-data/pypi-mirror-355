from __future__ import annotations
from typing import TYPE_CHECKING
from django.db import models
from django.contrib.auth.models import User
from unicom.models.constants import channels
from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_email
from fa2svg.converter import revert_to_original_fa
import uuid
import re
from bs4 import BeautifulSoup
import base64
from .fields import DedupFileField, only_delete_file_if_unused
from unicom.services.get_public_origin import get_public_origin
import openai
from django.conf import settings

if TYPE_CHECKING:
    from unicom.models import Channel


class Message(models.Model):
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('html', 'HTML'),
        ('image', 'Image'),
        ('audio', 'Audio'),
    ]
    id = models.CharField(max_length=500, primary_key=True)
    channel = models.ForeignKey('unicom.Channel', on_delete=models.CASCADE)
    platform = models.CharField(max_length=100, choices=channels)
    sender = models.ForeignKey('unicom.Account', on_delete=models.RESTRICT)
    user = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, blank=True)
    chat = models.ForeignKey('unicom.Chat', on_delete=models.CASCADE, related_name='messages')
    is_outgoing = models.BooleanField(null=True, default=None, help_text="True for outgoing messages, False for incoming, None for internal")
    sender_name = models.CharField(max_length=100)
    subject = models.CharField(max_length=512, blank=True, null=True, help_text="Subject of the message (only for email messages)")
    text = models.TextField()
    html = models.TextField(
        blank=True, null=True,
        help_text="Full HTML body (only for email messages)"
    )
    to  = ArrayField(
        base_field=models.EmailField(validators=[validate_email]),
        blank=True,
        default=list,
        help_text="List of To: addresses",
    )
    cc  = ArrayField(
        base_field=models.EmailField(validators=[validate_email]),
        blank=True,
        default=list,
        help_text="List of Cc: addresses",
    )
    bcc = ArrayField(
        base_field=models.EmailField(validators=[validate_email]),
        blank=True,
        default=list,
        help_text="List of Bcc: addresses",
    )
    media = models.FileField(upload_to='media/', blank=True, null=True)
    reply_to_message = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    timestamp = models.DateTimeField()
    time_sent = models.DateTimeField(null=True, blank=True)
    time_delivered = models.DateTimeField(null=True, blank=True)
    time_seen = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    raw = models.JSONField()
    media_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='text'
    )
    # Email tracking fields
    tracking_id = models.UUIDField(default=uuid.uuid4, null=True, blank=True, help_text="Unique ID for tracking email opens and clicks")
    time_opened = models.DateTimeField(null=True, blank=True, help_text="When the email was first opened")
    opened = models.BooleanField(default=False, help_text="Whether the email has been opened")
    time_link_clicked = models.DateTimeField(null=True, blank=True, help_text="When a link in the email was first clicked")
    link_clicked = models.BooleanField(default=False, help_text="Whether any link in the email has been clicked")
    clicked_links = ArrayField(
        base_field=models.URLField(),
        blank=True,
        null=True,
        default=list,
        help_text="List of links that have been clicked"
    )
    imap_uid = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="IMAP UID for marking as seen")

    def reply_with(self, msg_dict:dict) -> Message:
        """
        Reply to this message with a dictionary containing the response.
        The dictionary can contain 'text', 'html', 'file_path', etc.
        """
        from unicom.services.crossplatform.reply_to_message import reply_to_message
        return reply_to_message(self.channel, self, msg_dict)

    @property
    def original_content(self):
        return revert_to_original_fa(self.html) if self.platform == 'Email' else self.text

    @property
    def html_with_base64_images(self):
        """
        Returns the HTML content with all inline image shortlinks replaced by their original base64 data, if available.
        """
        if not self.html:
            return self.html
        soup = BeautifulSoup(self.html, 'html.parser')
        # Map shortlink src to base64 for all inline images
        images = {img.get_short_id(): img for img in getattr(self, 'inline_images', [])}
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src', '')
            # Extract short id from src (e.g., /i/abc123 or full URL)
            m = re.search(r'/i/([A-Za-z0-9]+)', src)
            if m:
                short_id = m.group(1)
                image_obj = images.get(short_id)
                if image_obj:
                    # Read file and encode as base64
                    data = image_obj.file.read()
                    image_obj.file.seek(0)
                    mime = 'image/png'  # Default
                    if hasattr(image_obj.file, 'file') and hasattr(image_obj.file.file, 'content_type'):
                        mime = image_obj.file.file.content_type
                    elif image_obj.file.name:
                        import mimetypes
                        mime = mimetypes.guess_type(image_obj.file.name)[0] or 'image/png'
                    b64 = base64.b64encode(data).decode('ascii')
                    img_tag['src'] = f'data:{mime};base64,{b64}'
        return str(soup)

    def as_llm_chat(self, depth=10, mode="chat", system_instruction=None, multimodal=True):
        """
        Returns a list of dicts for LLM chat APIs (OpenAI, Gemini, etc), each with 'role' and 'content'.
        - depth: max number of messages to include
        - mode: 'chat' (previous N in chat) or 'thread' (follow reply_to_message chain)
        - system_instruction: if provided, prepends a system message
        - multimodal: if True, includes media (image/audio) as content or URLs
        """
        def msg_to_dict(msg):
            # Determine role
            if msg.is_outgoing is True:
                role = "assistant"
            elif msg.is_outgoing is False:
                role = "user"
            else:
                role = "system"
            # Determine content
            content = None
            extra = {}
            if msg.media and multimodal and msg.media_type in ("image", "audio"):
                # Only use base64, do not use URLs
                b64 = None
                mime = None
                try:
                    msg.media.open('rb')
                    data = msg.media.read()
                    msg.media.seek(0)
                    import mimetypes
                    mime = mimetypes.guess_type(msg.media.name)[0] or 'application/octet-stream'
                    b64 = base64.b64encode(data).decode('ascii')
                except Exception:
                    b64 = None
                if msg.media_type == "image":
                    content = f"[Image attached]"
                    extra = {"image_base64": b64, "image_mime": mime}
                elif msg.media_type == "audio":
                    content = f"[Audio attached]"
                    extra = {"audio_base64": b64, "audio_mime": mime}
                else:
                    content = f"[File attached]"
                    extra = {"file_base64": b64, "file_mime": mime}
            elif msg.media_type == "html" and msg.html:
                content = msg.html
            else:
                content = msg.text or ""
            d = {"role": role, "content": content}
            d.update({k: v for k, v in extra.items() if v})
            return d

        messages = []
        if mode == "chat":
            qs = self.chat.messages.order_by("timestamp")
            idx = list(qs.values_list("id", flat=True)).index(self.id)
            start = max(0, idx - depth + 1)
            selected = list(qs[start:idx+1])
            for m in selected:
                messages.append(msg_to_dict(m))
        elif mode == "thread":
            chain = []
            cur = self
            for _ in range(depth):
                if not cur:
                    break
                chain.append(cur)
                cur = cur.reply_to_message
            for m in reversed(chain):
                messages.append(msg_to_dict(m))
        else:
            raise ValueError(f"Unknown mode: {mode}")
        if system_instruction:
            messages = [{"role": "system", "content": system_instruction}] + messages
        return messages

    def reply_using_llm(self, model: str, depth=10, mode="chat", system_instruction=None, multimodal=True, user=None, **kwargs):
        """
        Wrapper: Calls as_llm_chat, OpenAI ChatCompletion API, and reply_with.
        - model: OpenAI model string
        - depth, mode, system_instruction, multimodal: passed to as_llm_chat
        - user: Django user for reply_with
        - kwargs: extra params for OpenAI API
        Returns: The Message object created by reply_with
        """
        # Prepare messages for LLM
        messages = self.as_llm_chat(depth=depth, mode=mode, system_instruction=system_instruction, multimodal=multimodal)
        # Set API key
        openai.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        # Call OpenAI ChatCompletion API
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        # Get the LLM's reply (assume first choice)
        llm_msg = response.choices[0].message
        # Prepare reply dict
        if self.platform == 'Email':
            reply_dict = {'html': llm_msg.content}
        else:
            reply_dict = {'text': llm_msg.content}
        # Reply using reply_with
        return self.reply_with(reply_dict)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"{self.platform}:{self.chat.name}->{self.sender_name}: {self.text}"


class EmailInlineImage(models.Model):
    file = DedupFileField(upload_to='email_inline_images/', hash_field='hash')
    email_message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='inline_images', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content_id = models.CharField(max_length=255, blank=True, null=True, help_text='Content-ID for cid: references in HTML')
    hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text='SHA256 hash of file for deduplication')

    def delete(self, *args, **kwargs):
        only_delete_file_if_unused(self, 'file', 'hash')
        super().delete(*args, **kwargs)

    def get_short_id(self):
        # Use base62 encoding of PK for short URLs
        import string
        chars = string.digits + string.ascii_letters
        n = self.pk
        s = ''
        if n == 0:
            return chars[0]
        while n > 0:
            n, r = divmod(n, 62)
            s = chars[r] + s
        return s

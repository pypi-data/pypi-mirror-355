import asyncio
import time
from bson.objectid import ObjectId
from pymongo import MongoClient
from bs4 import BeautifulSoup

import requests  # Used in the synchronous HTML generator

import os
 
class MailBodyLinkGenerator:
    """
    Asynchronous utility to generate an HTML link from a given mail body ID.
    It fetches the mail document from the MongoDB collection
    in the database, retrieves the email content,
    cleans the HTML using BeautifulSoup, and then generates an HTML link via an external API.
    """
 
    def __init__(
        self,
      
        s3_prefix: str = "https://s3.ap-south-1.amazonaws.com/sm2.0-etl-prod-ap-south-1-274743989443/",
        html_generator: callable = None
    ):
       
        
        self.s3_prefix = s3_prefix
        # Use the provided html_generator or the default one below.
        self.html_generator = html_generator or self._default_html_generator
 
    def _default_html_generator(self, type_: str, obj_id: str, body: str) -> str:
        """
        Default function to generate an HTML link by making a synchronous HTTP POST call.
        """
        url = 'https://dev-api.siya.com/v1.0/s3bucket/generate-html'
        token = (
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
            'eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2Ii'
            'wiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsIml'
            'hdCI6MTc0MDgwODg2OH0sImlhdCI6MTc0MDgwODg2OCwiZXhwIjoxNzcyMzQ0ODY4fQ.'
            '1grxEO0aO7wfkSNDzpLMHXFYuXjaA1bBguw2SJS9r2M'
        )
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        filename = f"mail_{obj_id}_{int(time.time() * 1000)}"
        payload = {
            "type": type_,
            "fileName": filename,
            "body": body
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("url", "")
        except requests.exceptions.RequestException as e:
            print(f"HTML generation error: {e}")
            return ""
 

 
    def clean_html_content(self, html_content: str) -> str:
        """
        Clean up HTML content by removing unwanted tags and attributes using BeautifulSoup.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove HTML, head, and body tags
        for tag in soup.find_all(['html', 'head', 'body']):
            tag.unwrap()
        # Remove meta tags
        for meta in soup.find_all('meta'):
            meta.decompose()
        # Process image tags: remove those with auto-generated description; keep only 'src' and 'alt'
        for img in soup.find_all('img'):
            alt_text = img.get('alt', '').lower()
            if "description automatically generated" in alt_text:
                img.decompose()
            else:
                img.attrs = {k: v for k, v in img.attrs.items() if k in ['src', 'alt']}
        # Remove anchor tags with href starting with 'cid:'
        for a in soup.find_all('a'):
            if a.get('href', '').startswith('cid:'):
                a.decompose()
        return soup.decode_contents()
 
 
    async def generate_mail_link(self, mail_doc: dict) -> str:
       
        body_content = mail_doc.get("Body", "")
        
        # If Body is just a placeholder like "html part", try using BodyPreview instead
        if body_content in ["html part", "", None]:
            body_content = mail_doc.get("BodyPreview", "")
        
        if not body_content:
            print("No body content found in the document")
            return ""
        
       
        if body_content.strip().startswith("<"):
            cleaned_content = self.clean_html_content(body_content)
        else:
            # Convert plain text to HTML by wrapping in paragraph tags
            cleaned_content = "<p>" + body_content.replace("\n", "</p><p>") + "</p>"
        
        # Prepare metadata
        sender_name = mail_doc.get("SenderName", "Unknown")
        sender_email = mail_doc.get("SenderEmailAddress", "Unknown")
        subject = mail_doc.get("Subject", "No Subject")
        
        # Use DateTimeSent or another date field as available
        date_fields = ["DateTimeSent", "DateTimeReceived", "createdAt"]
        send_date = "Unknown"
        for field in date_fields:
            if field in mail_doc and mail_doc[field]:
                send_date = mail_doc[field]
                break
        
        # Handle recipient fields with new format
        to_names = mail_doc.get("ToRecipients_Names", "").split(", ") if mail_doc.get("ToRecipients_Names") else ["No recipients"]
        to_emails = mail_doc.get("ToRecipients_EmailAddresses", "").split(", ") if mail_doc.get("ToRecipients_EmailAddresses") else []
        cc_names = mail_doc.get("CcRecipients_Names", "").split(", ") if mail_doc.get("CcRecipients_Names") else ["No CC recipients"]
        cc_emails = mail_doc.get("CcRecipients_EmailAddresses", "").split(", ") if mail_doc.get("CcRecipients_EmailAddresses") else []
        
        def format_recipients(names, emails):
            if not names or names in (["No recipients"], ["No CC recipients"]):
                return names[0] if names else ""
            if isinstance(names, list) and isinstance(emails, list) and emails:
                return ", ".join(f"{n} <{e}>" for n, e in zip(names, emails))
            return ", ".join(names)
        
        formatted_to = format_recipients(to_names, to_emails)
        formatted_cc = format_recipients(cc_names, cc_emails)
        
        # Add attachments information if available
        attachments_section = ""
        if mail_doc.get("attachments") and isinstance(mail_doc["attachments"], list) and mail_doc["attachments"]:
            attachments_section = "\n\n**Attachments:**\n"
            for idx, attach_url in enumerate(mail_doc["attachments"], 1):
                filename = attach_url.split("/")[-1]
                attachments_section += f"{idx}. {filename}  \n"
        
        # Create metadata in Markdown format with explicit line breaks
        # Using double space at the end of each line to force line breaks in markdown
        metadata_markdown = f"""**From:** {sender_name} <{sender_email}>  \n
**Subject:** {subject}  \n
**Date:** {send_date}  \n
**To:** {formatted_to}  \n
**CC:** {formatted_cc}  \n{attachments_section}
 
---
 
"""
        # Combine metadata with the cleaned content
        combined_content = f"{metadata_markdown}{cleaned_content}"
        
        # Generate a unique filename using mailbody_id and current timestamp
        unique_id = f"{mail_doc.get("_id")}_{int(time.time() * 1000)}"
        
        # Run the synchronous HTML generator in an executor
        loop = asyncio.get_running_loop()
        html_link = await loop.run_in_executor(
            None, lambda: self.html_generator("casefile_report", unique_id, combined_content)
        )
        return html_link
 
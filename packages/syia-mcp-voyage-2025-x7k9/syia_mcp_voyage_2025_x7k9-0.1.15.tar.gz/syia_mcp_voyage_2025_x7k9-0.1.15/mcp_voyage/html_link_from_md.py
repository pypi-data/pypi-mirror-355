import requests
import time
import logging
from typing import Optional
from . import logger

def markdown_to_html_link(
    markdown_content: str, 
    filename_prefix: str = "document", 
    document_type: str = "casefile_report"
) -> Optional[str]:
    """
    Convert markdown content to an HTML link using the API endpoint.
    Fixed version based on the working _default_html_generator implementation.
    
    Args:
        markdown_content (str): The markdown content to convert to HTML
        filename_prefix (str): Prefix for the generated filename (default: "document")
        document_type (str): Type of document for API (default: "casefile_report")
        
    Returns:
        str or None: The generated HTML link URL, or None if conversion failed
    """
    if not markdown_content:
        logger.error("Cannot generate HTML link: No markdown content provided")
        return None
    
    # Use the exact same implementation as the working _default_html_generator
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
    
    # Use the same filename format as the working implementation
    filename = f"mail_{filename_prefix}_{int(time.time() * 1000)}"
    
    payload = {
        "type": document_type,
        "fileName": filename,
        "body": markdown_content
    }
    
    try:
        logger.info(f"Converting markdown to HTML link with filename: {filename}")
        logger.info(f"Content length: {len(markdown_content)} characters")
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        html_url = data.get("url", "")
        
        if html_url:
            logger.info(f"Successfully generated HTML link: {html_url}")
            return html_url
        else:
            logger.error("API response did not contain a URL")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTML generation error: {e}")
        return None

def create_sample_markdown() -> str:
    """
    Create a sample markdown document for testing.
    
    Returns:
        str: Sample markdown content
    """
    sample_markdown = """# Sample Document

**From:** John Doe <john.doe@example.com>  
**Subject:** Important Meeting Notes  
**Date:** 2024-01-15  
**To:** Team <team@example.com>  

---

## Meeting Summary

This is a **sample document** with some markdown formatting:

### Key Points:
1. First important point
2. Second critical item
3. Third action item

### Code Example:
```python
def hello_world():
    print("Hello, World!")
```

### Links and Lists:
- [Example Link](https://example.com)
- *Italic text*
- **Bold text**

> This is a blockquote with important information.

### Table:
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Info A   | Info B   | Info C   |

---

**Attachments:**
1. document1.pdf  
2. spreadsheet.xlsx  

*End of document*
"""
    return sample_markdown

def create_email_markdown(sender_name: str, sender_email: str, subject: str, 
                         to_recipients: str, cc_recipients: str = "", 
                         date: str = "", body_content: str = "", 
                         attachments: list = None) -> str:
    """
    Create an email-style markdown document with metadata.
    
    Args:
        sender_name: Name of the sender
        sender_email: Email address of the sender
        subject: Email subject
        to_recipients: To recipients
        cc_recipients: CC recipients (optional)
        date: Date of the email
        body_content: Main body content
        attachments: List of attachment filenames (optional)
        
    Returns:
        str: Formatted markdown content
    """
    # Build metadata section
    metadata_lines = [
        f"**From:** {sender_name} <{sender_email}>  ",
        f"**Subject:** {subject}  ",
        f"**Date:** {date}  ",
        f"**To:** {to_recipients}  "
    ]
    
    if cc_recipients:
        metadata_lines.append(f"**CC:** {cc_recipients}  ")
    
    # Add attachments if provided
    attachments_section = ""
    if attachments:
        attachments_section = "\n\n**Attachments:**\n"
        for idx, filename in enumerate(attachments, 1):
            attachments_section += f"{idx}. {filename}  \n"
    
    # Combine everything
    markdown_content = "\n".join(metadata_lines)
    markdown_content += attachments_section
    markdown_content += "\n\n---\n\n"
    markdown_content += body_content
    
    return markdown_content

def main():
    """
    Example usage of the markdown_to_html_link function.
    """
    print("🔧 Markdown to HTML Link Converter (Fixed)")
    print("=" * 45)
    
    # Option 1: Use sample markdown
    print("\n1. Converting sample markdown...")
    sample_content = create_sample_markdown()
    
    sample_link = markdown_to_html_link(
        markdown_content=sample_content,
        filename_prefix="sample_document",
        document_type="casefile_report"
    )
    
    if sample_link:
        print(f"✅ Sample document converted successfully!")
        print(f"🔗 HTML Link: {sample_link}")
    else:
        print("❌ Failed to convert sample document")
    
    # Option 2: Convert email-style markdown
    print("\n2. Converting email-style markdown...")
    email_content = create_email_markdown(
        sender_name="Alice Johnson",
        sender_email="alice@company.com",
        subject="Project Update - Q1 Results",
        to_recipients="team@company.com",
        cc_recipients="manager@company.com",
        date="2024-01-15 14:30:00",
        body_content="""## Project Status Update

I'm pleased to report that we've completed **Phase 1** of the project ahead of schedule.

### Key Achievements:
- ✅ Database migration completed
- ✅ API endpoints tested and deployed
- ✅ User interface redesigned
- ✅ Performance improvements implemented

### Next Steps:
1. Begin Phase 2 development
2. Schedule stakeholder review
3. Plan user acceptance testing

Please let me know if you have any questions.

Best regards,  
Alice""",
        attachments=["project_report.pdf", "timeline.xlsx"]
    )
    
    email_link = markdown_to_html_link(
        markdown_content=email_content,
        filename_prefix="email_update",
        document_type="casefile_report"
    )
    
    if email_link:
        print(f"✅ Email document converted successfully!")
        print(f"🔗 HTML Link: {email_link}")
    else:
        print("❌ Failed to convert email document")
    
    # Option 3: Convert custom markdown
    print("\n3. Converting custom markdown...")
    custom_markdown = """# My Custom Document

This is a **custom markdown** document with some content:

## Features:
- Easy to use ✨
- Fast conversion ⚡
- Reliable API 🔧

### Code Sample:
```javascript
function greetUser(name) {
    console.log(`Hello, ${name}!`);
}
```

*Created with the fixed markdown_to_html_link utility*
"""
    
    custom_link = markdown_to_html_link(
        markdown_content=custom_markdown,
        filename_prefix="custom_doc",
        document_type="casefile_report"
    )
    
    if custom_link:
        print(f"✅ Custom document converted successfully!")
        print(f"🔗 HTML Link: {custom_link}")
    else:
        print("❌ Failed to convert custom document")

if __name__ == "__main__":
    main() 
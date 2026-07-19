from pydantic import BaseModel
from typing import Optional

class SettingsUpdate(BaseModel):
    company_name:Optional[str]=None
    gst_percentage:Optional[float]=None
    email_smtp_host:Optional[str]=None
    email_smtp_port:Optional[int]=None
    invoice_footer:Optional[str]=None
    
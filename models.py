from pydantic import BaseModel
from typing import Optional

class UserAccountContext(BaseModel):
    user_id: str
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    food_preferences: Optional[str] = None
    cravings: Optional[str] = None

class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str

class TechnicalOutputGuardRailOutput(BaseModel):
    contains_off_topic: bool
    contains_menu_data: bool
    contains_order_data: bool
    contains_table_reservation_data: bool
    reason: str


class HandoffData(BaseModel):

    to_agent_name: str
    menu_description: str
    order: str
    table_reservation: str
    reason: str

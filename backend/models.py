from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from database import Base


class Job(Base):
    __tablename__ = "hobs"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="OPEN")
    type = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    raw_message = Column(Text, nullable=True)
    driver_phone = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    vehicle_info = Column(String, nullable=True)
    vehicle_vin = Column(String, nullable=True)
    location = Column(String, nullable=True)
    incident_lat = Column(Float, nullable=True)
    incident_lng = Column(Float, nullable=True)
    assigned_vendor_name = Column(String, nullable=True)
    assigned_vendor_phone = Column(String, nullable=True)
    vendor_eta_minutes = Column(Integer, nullable=True)
    actions = Column(Text, default="[]")
    agent_runs = Column(Text, default="[]")
    source = Column(String, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    service_types = Column(Text, default="[]")
    coverage_area = Column(String, nullable=True)
    rating = Column(Float, default=4.5)
    avg_response_min = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class GeographicalArea(Base):
    __tablename__ = "geographical_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g., "Miền Nam", "TP.HCM"

    groups = relationship("SalesGroup", back_populates="area")

class SalesGroup(Base):
    __tablename__ = "sales_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Hierarchy: Parent group for tree structure
    parent_id = Column(Integer, ForeignKey("sales_groups.id"), nullable=True)

    # Each group has one team lead
    lead_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # Geographical area assignment
    area_id = Column(Integer, ForeignKey("geographical_areas.id"), nullable=True)

    # Relationships
    children = relationship("SalesGroup", backref="parent", remote_side=[id])
    area = relationship("GeographicalArea", back_populates="groups")
    employees = relationship("Employee", back_populates="group")
    lead = relationship("Employee", foreign_keys=[lead_id])

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # e.g., "Staff", "TeamLead", "Director"

    # Each employee belongs to exactly one group
    group_id = Column(Integer, ForeignKey("sales_groups.id"), nullable=True)

    group = relationship("SalesGroup", back_populates="employees")

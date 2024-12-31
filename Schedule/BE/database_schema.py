
from sqlalchemy import UniqueConstraint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Models
class PlatformLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    scheduled_message_id = db.Column(db.Integer, db.ForeignKey('scheduled_message.id', ondelete='CASCADE'), nullable=False)
    log_message = db.Column(db.String(200))
    direction = db.Column(db.String(20), nullable=False, default='outgoing')  # 'incoming' or 'outgoing'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner_account.id', ondelete='CASCADE'), nullable=False)  # Link to OwnerAccount
    platform_name = db.Column(db.String(50), nullable=False)  # 'whatsapp', 'telegram', 'gmail'
    login_id = db.Column(db.String(50), nullable=False)
    login_credentials = db.Column(db.Text, nullable=False)  # Encrypted credentials
    status = db.Column(db.String(20), default='active')  # Active/inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = db.relationship('OwnerAccount', back_populates='platforms')  # Relationship to OwnerAccount


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    owner_id = db.Column(
        db.Integer, 
        db.ForeignKey('owner_account.id', ondelete='CASCADE'),
        unique=True, 
        nullable=True
    )  # Break the cascading delete cycle by setting to NULL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    users = db.relationship('User', back_populates='organization')
    contacts = db.relationship('Contact', back_populates='organization')
    contact_groups = db.relationship('ContactGroup', back_populates='organization')
    group_members = db.relationship('GroupMember', back_populates='organization')


class OwnerAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )  # Allow user deletion to cascade
    organization_id = db.Column(
        db.Integer, 
        db.ForeignKey('organization.id', ondelete='CASCADE'),
        nullable=True
    )  # Prevent cascading deletes from causing a cycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    platforms = db.relationship('Platform', back_populates='owner', cascade='all, delete-orphan')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'employee'
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    contacts = db.relationship('Contact', back_populates='creator')
    contact_groups = db.relationship('ContactGroup', back_populates='creator')
    organization = db.relationship('Organization', back_populates='users')


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(4096), nullable=True)
    image = db.Column(db.String(2048), nullable=True)
    address = db.Column(db.String(4096), nullable=True)
    category = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(256), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships for convenience
    creator = db.relationship('User', back_populates='contacts')
    organization = db.relationship('Organization', back_populates='contacts')
    groups = db.relationship('GroupMember', back_populates='contacts', cascade='all, delete-orphan')

    def __str__(self) -> str:
        return self.name


class ContactGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships for convenience
    creator = db.relationship('User', back_populates='contact_groups')
    organization = db.relationship('Organization', back_populates='contact_groups')
    members = db.relationship('GroupMember', back_populates='contact_groups', cascade='all, delete-orphan')


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('contact_group.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships for convenience
    contact_groups = db.relationship('ContactGroup', back_populates='members')
    contacts = db.relationship('Contact', back_populates='groups')
    organization = db.relationship('Organization', back_populates='group_members')


class ScheduledMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)  # 'individual', 'group'
    recipient_id = db.Column(db.Integer, nullable=False)  # Contact ID or Group ID
    frequency = db.Column(db.Integer, default=0)  # Contact ID or Group ID
    message_body = db.Column(db.Text, nullable=False)
    platform = db.Column(
        db.Integer, 
        db.ForeignKey('platform.id', ondelete='CASCADE'),
        nullable=False
    )
    scheduled_time = db.Column(db.DateTime, nullable=False)
    datasource = db.Column(db.JSON, nullable=True)  # Store the entire datasource configuration
    excel_filename = db.Column(db.String, nullable=True)  # Store the unique filename of the Excel file
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'sent', 'canceled', 'failed'
    sent_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_name_per_organization'),
    )

# Conversation model
class Conversation(db.Model):
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed'

class IncomingMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    received_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='unread')  # 'unread', 'read', 'responded'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    # TODO: This would be helpful if the message actually sent from watsapp server(webhook notification)
    status = db.Column(db.String(50), nullable=True)

class MessageResponseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    incoming_message_id = db.Column(db.Integer, db.ForeignKey('incoming_message.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    response_message = db.Column(db.Text, nullable=False)
    response_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

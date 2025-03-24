
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
    messageid = db.Column(db.String(200), nullable=True, default=None)
    status = db.Column(db.String(20), nullable=False, default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner_account.id', ondelete='CASCADE'), nullable=False)  # Link to OwnerAccount
    platform_name = db.Column(db.String(50), nullable=False)  # 'whatsapp', 'telegram', 'gmail'
    login_id = db.Column(db.String(50), nullable=False)
    app_id = db.Column(db.String(50), nullable=False)
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
    robo_name = db.Column(db.String(100), unique=True, nullable=False)
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
    uuid = db.Column(db.Text, nullable=True)
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
    description = db.Column(db.String(4096), nullable=True)
    category = db.Column(db.String(256), nullable=True)
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
    frequency = db.Column(db.Integer, default=-1)  # Contact ID or Group ID
    message_body = db.Column(db.Text, nullable=False)
    platform = db.Column(
        db.Integer, 
        db.ForeignKey('platform.id', ondelete='CASCADE'),
        nullable=False
    )
    scheduled_time = db.Column(db.DateTime, nullable=False)
    datasource = db.Column(db.JSON, nullable=True)  # Store the entire datasource configuration
    excel_filename = db.Column(db.String, nullable=True)  # Store the unique filename of the Excel file
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'canceled', 'failed'
    msg_status = db.Column(db.String(20), default='') # 'sent_to_server', 'delivered', 'read', 'sent', 'failed'
    sent_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messageid = db.Column(db.Text, nullable=True)
    template = db.Column(db.Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_name_per_organization'),
    )

############ Conversation model ############
class Conversation(db.Model):
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    open_by = db.Column(db.String(20), default='customer')  # 'active', 'closed'
    closed_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    closed_reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='new')  # 'active', 'closed'
    

class IncomingMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    received_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='unread')  # 'unread', 'read', 'responded'
    status_details = db.Column(db.Text, nullable=True) # Placeholder for now
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.contact_id,
            'conversation_id': self.conversation_id,
            'received_time': self.received_time.isoformat() if self.received_time else None,  # Convert datetime to ISO 8601 string
            'message_body': self.message_body,
            'status': self.status,
            "status_details": self.status_details,
            'type': 'customer'
        }

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
    status_details = db.Column(db.Text, nullable=True)
    messageid = db.Column(db.Text, nullable=True)
    template = db.Column(db.Text, nullable=True)

class MessageResponseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    incoming_message_id = db.Column(db.Integer, db.ForeignKey('incoming_message.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    response_message = db.Column(db.Text, nullable=False)
    response_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

############ Project Model ############
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False, unique=True)  # Project name
    description = db.Column(db.Text, nullable=True)  # Optional detailed description
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # User who created the project
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Project start date
    end_date = db.Column(db.DateTime, nullable=True)  # Optional project end date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp for creation
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Timestamp for last update

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'creator_id': self.creator_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,  # Convert datetime to ISO 8601 string
            'end_date': self.end_date.isoformat() if self.end_date else None,  # Convert datetime to ISO 8601 string
            'created_at': self.created_at.isoformat() if self.created_at else None,  # Convert datetime to ISO 8601 string
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,  # Convert datetime to ISO 8601 string
        }

############ Task Model ############
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False)  # New field
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Medium')  # 'Low', 'Medium', 'High'
    status = db.Column(db.String(20), nullable=False, default='Open')  # 'Open', 'In Progress', 'Closed'
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'creator_id': self.creator_id,
            'assignee_id': self.assignee_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,  # Convert datetime to ISO 8601 string
            'created_at': self.created_at.isoformat() if self.created_at else None,  # Convert datetime to ISO 8601 string
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,  # Convert datetime to ISO 8601 string
        }

############ TaskHistory Model ############
class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # 'Status updated', 'Reassigned', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)  # JSON string for additional details

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,  # Convert datetime to ISO 8601 string
            'details': self.details,
        }

############ TaskComment Model ############
class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    comment_body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'comment_body': self.comment_body,
            'created_at': self.created_at.isoformat() if self.created_at else None,  # Convert datetime to ISO 8601 string
        }


############ Keylogger Model ############
class KeyLogger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    emp_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=False)
    date = db.Column(db.Text, nullable=False)
    app_details = db.Column(db.Text, nullable=False)
    idle_time = db.Column(db.Integer, nullable=False)

class Uuid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False)
    uuid = db.Column(db.Text, unique=True, nullable=False)

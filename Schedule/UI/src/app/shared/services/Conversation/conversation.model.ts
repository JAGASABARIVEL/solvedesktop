export interface MessageModel {
    id: number,
    type: 'customer' | 'org',
    message_body: string,
    status: string,
    received_time: Date,
    sent_time: Date;
}


export interface ConversationModel {
    contact: {
        id: number,
        name: string,
        phone: string
    },
    conversation_id: number,
    assigned: {
        id: number,
        name: string
    },
    created_at: Date,
    organization_id: number,
    status: string,
    messages: MessageModel[],
    isDropdownVisible: boolean
}

  
export interface UserMessages {
    id: number;
    name: string;
    phone: string;
    img: string;
    status: string;
    messages: MessageModel[];
}

export interface ConversationResponseModel {
    conversation_id: number,
    message_body: string,
    user_id: number
}
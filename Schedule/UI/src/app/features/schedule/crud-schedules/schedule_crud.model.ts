export interface ScheduleModel {
    id: number,
    name: string,
    recipient_name: string,
    recipient_type: string,
    platform_name: string,
    frequency: Frequencies,
    message_body: string,
    created_by: UserModel,
    created_at: any,
    scheduled_time: any,
    status: string
}

export interface UserModel {
    name: string,
    img: string
}

export enum Frequencies {
    No = 0,
    Daily = 1,
    Weekly = 2,
    Monthly = 3,
    Quarterly = 4,
    HalfYearly = 5,
    Yearly = 6
}
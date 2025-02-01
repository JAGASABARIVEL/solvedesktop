export interface MessageHistoryModel {
    id: number,
    schedule_name: string,
    recipient: string,
    send_date: Date,
    status: string,
    status_details: string
}
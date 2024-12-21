export interface DataSourceModel {
    name: {
        type: string,
        file_upload: string,
    }
}

export interface ComposeMessageModel {
    name: string
    uploaded_excel: File,
    organization_id: number,
    platform: number,
    user_id: number,
    recipient_type: string,
    recipient_id: number,
    message_body: string,
    scheduled_time: string,
    datasource: DataSourceModel
}
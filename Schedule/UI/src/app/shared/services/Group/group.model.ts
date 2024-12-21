export interface CreateGroupMode {
    name: string,
    organization_id : number,
    created_by: number
}

export interface AddContactToGroupModel {
    contact_id: number,
    organization_id: number,
    group_id: number
}

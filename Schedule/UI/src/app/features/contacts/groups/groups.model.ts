
export interface MemberModel {
    group_id: number,
    organization_id: number
    created_at: Date,
    id: number,
    contact_id: number,
    contact_name: string,
    contact_phone: number
}

export interface GroupModel {
    id: number,
    organization_id: number,
    name: string,
    description: string,
    total: number,
    category: string,
    created_by: number,
    members: MemberModel[]

}


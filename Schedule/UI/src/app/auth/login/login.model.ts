export interface LoginModel {
    phone: string
    password: string
    uuid: string
}

export interface LoginResponseModel {
    id: number,
    name: string,
    email: string,
    phone: string,
    role: string,
    organization: number
}
export interface OwnerSignup {
    name: string,
    phone: string,
    email: string,
    uuid: string,
    user_type: string,
    organization: string,
    platform_name: string,
    login_id: string,
    platform_login_credentials: string,
    robo_name: string,
    password: string
}

export interface EmployeeSignup {
    name: string,
    phone: string,
    email: string,
    uuid: string,
    user_type: string,
    organization: string,
    password: string
}
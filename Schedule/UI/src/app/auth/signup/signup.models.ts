export interface OwnerSignup {
    name: string;
    phone: string;
    email: string;
    user_type: string;
    organization: string;
    platform_name: string,
    login_id: string,
    platform_login_credentials: string,
    password: string;
}

export interface EmployeeSignup {
    name: string;
    phone: string;
    email: string;
    user_type: string;
    organization: string;
    password: string;
}
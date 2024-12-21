/**
 * Example usage:

const authUrls = new AuthUrl();
console.log(authUrls.login); // http://localhost:5000/login

const contactUrls = new ContactUrl();
console.log(contactUrls.create); // http://localhost:5000/contacts/create
*/

const BASE_URL = "http://localhost";
const PORT = ":5000";

const LOGIN_URI = "/login";
const SIGNUP_URI = "/signup";
const FORGOT_PASSWORD_URI = "/forgot_password";
// Mostly not needed since its users phone
const FORGOT_USERNAME_URI = "/forgot_username";

// Contact CRUD endpoints
const CONTACT_URI = "/contacts";
const CONTACT_CREATE_URI = "/contacts";
const CONTACT_UPDATE_URI = "/contacts";
const CONTACT_DELETE_URI = "/contacts";
const CONTACT_FETCH_URI = "/contacts";

// Group CRUD endpoints
const GROUP_URI = "/groups";
const GROUP_CREATE_URI = "/groups";
const GROUP_UPDATE_URI = "/groups";
const GROUP_DELETE_URI = "/groups";
const GROUP_FETCH_URI = "/groups";
const GROUP_ADD_MEMBERS = "/add_contact";

// Platform CRUD endpoints
const PLATFORM_URI = "/platforms";
const PLATFORM_CREATE_URI = "/platforms";
const PLATFORM_UPDATE_URI = "/platforms";
const PLATFORM_DELETE_URI = "/platforms";
const PLATFORM_FETCH_URI = "/platforms";

// Schedule CRUD endpoints
const SCHEDULE_URI = "/schedule";
const SCHEDULE_CREATE_URI = "/schedule";
const SCHEDULE_UPDATE_URI = "/schedule";
const SCHEDULE_DELETE_URI = "/schedule";
const SCHEDULE_FETCH_URI = "/schedule";

export class Url {
    url = `${BASE_URL}${PORT}`;
}

export class AuthUrl extends Url {
    get login() {
        return `${this.url}${LOGIN_URI}`;
    }

    get signup() {
        return `${this.url}${SIGNUP_URI}`;
    }

    get forgotPassword() {
        return `${this.url}${FORGOT_PASSWORD_URI}`;
    }

    get forgotUsername() {
        return `${this.url}${FORGOT_USERNAME_URI}`;
    }
}

export class ContactUrl extends Url {
    get base() {
        return `${this.url}${CONTACT_URI}`;
    }

    get create() {
        return `${this.url}${CONTACT_CREATE_URI}`;
    }

    get update() {
        return `${this.url}${CONTACT_UPDATE_URI}`;
    }

    get delete() {
        return `${this.url}${CONTACT_DELETE_URI}`;
    }

    get fetch() {
        return `${this.url}${CONTACT_FETCH_URI}`;
    }
}

export class GroupUrl extends Url {
    get base() {
        return `${this.url}${GROUP_URI}`;
    }

    get create() {
        return `${this.url}${GROUP_CREATE_URI}`;
    }

    get update() {
        return `${this.url}${GROUP_UPDATE_URI}`;
    }

    get delete() {
        return `${this.url}${GROUP_DELETE_URI}`;
    }

    get fetch() {
        return `${this.url}${GROUP_FETCH_URI}`;
    }

    get addMembers() {
        return `${this.url}${GROUP_URI}${GROUP_ADD_MEMBERS}`;
    }
}

export class PlatformUrl extends Url {
    get base() {
        return `${this.url}${PLATFORM_URI}`;
    }

    get create() {
        return `${this.url}${PLATFORM_CREATE_URI}`;
    }

    get update() {
        return `${this.url}${PLATFORM_UPDATE_URI}`;
    }

    get delete() {
        return `${this.url}${PLATFORM_DELETE_URI}`;
    }

    get fetch() {
        return `${this.url}${PLATFORM_FETCH_URI}`;
    }
}

export class ScheduleUrl extends Url {
    get base() {
        return `${this.url}${SCHEDULE_URI}`;
    }

    get create() {
        return `${this.url}${SCHEDULE_CREATE_URI}`;
    }

    get update() {
        return `${this.url}${SCHEDULE_UPDATE_URI}`;
    }

    get delete() {
        return `${this.url}${SCHEDULE_DELETE_URI}`;
    }

    get fetch() {
        return `${this.url}${SCHEDULE_FETCH_URI}`;
    }
}


export const supported_contact_types = [
    {"name": "User", "value": "user"},
    {"name": "Group", "value": "group"}
];

export const supported_frequencies = [
    {label: "Daily", value: 0},
    {label: "Weekly", value: 1},
    {label: "Monthly", value: 2},
    {label: "Quarterly", value: 3},
    {label: "Half-Yearly", value: 4},
    {label: "Yearly", value: 5},
];

export const supported_datasource = [
    {"name": "excel"}
];
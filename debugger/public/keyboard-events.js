export class KeyboardEvents {
    constructor() {
        this.handlers = {};

        document.addEventListener("keyup", event => this.OnKey(event.key, true));
        document.addEventListener("keydown", event => this.OnKey(event.key, false));
    }

    AddHandler(key, handler) {
        if (!this.handlers[key])
            this.handlers[key] = []

        this.handlers[key].push(handler);
    }

    RemoveHandler(key, handler) {
        if (this.handlers[key]) {
            this.handlers[key] = this.handlers[key].filter(handler => !this.handlers[key].includes(handler));
        }
    }

    OnKey(key, up) {
        if (this.handlers[key]) {
            this.handlers[key].forEach(handler => {
                handler(up);
            });
        }
    }
}
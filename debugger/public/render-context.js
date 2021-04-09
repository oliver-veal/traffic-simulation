export class RenderContext {
    constructor(renderElement) {
        this.renderElement = renderElement;

        this.two = new Two({
            fullscreen: true,
            autostart: true
        }).appendTo(renderElement);

        this.mouse = {
            current: new Two.Vector(),
            previous: new Two.Vector()
        };

        this.zui = new Two.ZUI(this.two.scene);
        // The min and max zoom levels for the stage
        this.zui.addLimits(0.06, 8);

        let mousemove = e => {
            this.mouse.current.set(e.clientX, e.clientY);

            let dx = this.mouse.current.x - this.mouse.previous.x;
            let dy = this.mouse.current.y - this.mouse.previous.y;

            // To Pan
            this.zui.translateSurface(dx, dy);

            this.mouse.previous.copy(this.mouse.current);
        }

        let mouseup = e => {
            window.removeEventListener('mousemove', mousemove, false);
            window.removeEventListener('mouseup', mouseup, false);
        }

        let mousedown = e => {
            this.mouse.current.set(e.clientX, e.clientY);
            this.mouse.previous.copy(this.mouse.current);

            window.addEventListener('mousemove', mousemove, false);
            window.addEventListener('mouseup', mouseup, false);
        }

        let scroll = e => {
            e.stopPropagation();
            e.preventDefault();

            let dy = (e.wheelDeltaY || - e.deltaY) / 1000;

            // To zoom by an increment
            this.zui.zoomBy(dy, e.clientX, e.clientY);
        }

        this.two.renderer.domElement.addEventListener('mousewheel', scroll, false);
        this.two.renderer.domElement.addEventListener('mousedown', mousedown, false);

        this.zui.zoomBy(-1, 0, 0);
        this.zui.translateSurface(window.innerWidth / 2, window.innerHeight / 2);
    }
}
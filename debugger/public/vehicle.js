const styles = {
    family: 'proxima-nova, sans-serif',
    size: 50,
    leading: 50,
    weight: 900,

};

export class Vehicle {
    constructor(data, two) {
        this.id = data.id;
        this.type = data.type;
        this.width = data.width * 100;
        this.length = data.length * 100;
        this.wheelBase = data.wheelBase * 100;
        this.xoffset = this.length / 2 - ((this.length - this.wheelBase) / 2);
        this.position = new Two.Vector(data.position.x * 100, data.position.y * 100);
        this.velocity = new Two.Vector(data.velocity.x, data.velocity.y);
        this.rotation = data.rotation;
        this.angularVelocity = data.angularVelocity;
        this.two = two;

        this.corners = data.corners;
    }

    AddToScene() {
        this.shape = new Two.RoundedRectangle(this.xoffset, 0, this.length, this.width, 10);
        this.center = new Two.Circle(0, 0, 1);
        this.text = new Two.Text(this.id, 0, 0, styles);
        this.center.opacity = 0
        this.body = this.two.makeGroup(this.shape, this.center, this.text);
        this.body.translation = this.position;
        this.body.rotation = this.rotation;
        this.shape.fill = "transparent";
        this.body.linewidth = 5;
        this.two.add(this.body);

        this.c0 = this.two.makeCircle(this.corners[0].x * 100, this.corners[0].y * 100, 2);
        this.c1 = this.two.makeCircle(this.corners[1].x * 100, this.corners[1].y * 100, 2);
        this.c2 = this.two.makeCircle(this.corners[2].x * 100, this.corners[2].y * 100, 2);
        this.c3 = this.two.makeCircle(this.corners[3].x * 100, this.corners[3].y * 100, 2);
    }

    RemoveFromScene() {
        this.two.remove(this.body)
        this.two.remove(this.c0)
        this.two.remove(this.c1)
        this.two.remove(this.c2)
        this.two.remove(this.c3)
    }

    Update(data) {
        // this.position.set(this.position.x, this.position.y - 10);
        this.position.set(data.position.x * 100, data.position.y * 100);
        this.velocity.set(data.velocity.x, data.velocity.y);
        this.rotation = data.rotation;
        this.angularVelocity = data.angularVelocity;
        this.body.rotation = this.rotation;

        this.corners = data.corners;

        this.c0.translation.set(this.corners[0].x * 100, this.corners[0].y * 100);
        this.c1.translation.set(this.corners[1].x * 100, this.corners[1].y * 100);
        this.c2.translation.set(this.corners[2].x * 100, this.corners[2].y * 100);
        this.c3.translation.set(this.corners[3].x * 100, this.corners[3].y * 100);

        // console.log("========================");
        // console.log(`Velocity: x: ${Math.round(this.velocity.x)}, y: ${Math.round(this.velocity.y)}`);
        // console.log(`Position: x: ${Math.round(this.position.x)}, y: ${Math.round(this.position.y)}`);
        // console.log(this.id, this.type, this.position, this.velocity);
    }

    Interpolate(dt) {
        this.position.set(this.position.x + (this.velocity.x * dt), this.position.y + (this.velocity.y * dt));
        // this.rotation += this.angularVelocity * dt;
        // console.log(`Velocity: x: ${Math.round(this.velocity.x)}, y: ${Math.round(this.velocity.y)}`);
        // console.log(`Position: x: ${Math.round(this.position.x)}, y: ${Math.round(this.position.y)}`);
        // this.body.rotation = this.rotation;
        
        // console.log("Interpolating to: " + this.position);
    }
}
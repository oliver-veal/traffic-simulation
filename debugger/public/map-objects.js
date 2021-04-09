export class MapObject {
    constructor(data, two) {
        this.data = data;
        this.id = data.id;
        this.two = two;
    }
}

const styles = {
    family: 'proxima-nova, sans-serif',
    size: 200,
    leading: 50,
    weight: 900,

};

export class Lane extends MapObject {
    constructor(data, two) {
        super(data, two);
        this.position = new Two.Vector(data.position.x * 100, data.position.y * 100);
        this.orientation = data.orientation
        this.type = data.type;
        this.width = data.width * 100;
        this.length = data.length * 100;
    }

    AddToScene() {
        this.shape = new Two.Rectangle(0, 0, this.length, this.width);
        this.shape.rotation = this.orientation * Math.PI / 180;
        this.text = new Two.Text(this.id, 0, 0, styles);
        this.body = this.two.makeGroup(this.shape, this.text);
        this.body.translation = this.position;
        this.shape.linewidth = 5;
        this.text.linewidth = 10;
        this.body.stroke = this.type === "ENTRY" ? "#666666" : "#BDBDBD";
        this.body.fill = this.type === "ENTRY" ? "rgba(0, 0, 0, 0.1)" : "rgba(0, 0, 0, 0.05)";
        this.two.add(this.body);
    }

}

const LIGHT_COLORS = {
    1: "#0DFF39",
    2: "#FFA523",
    3: "#FF0000"
}

export class TrafficLight extends MapObject {
    constructor(data, two) {
        super(data, two);
        this.position = new Two.Vector(data.position.x * 100, data.position.y * 100);
        this.orientation = data.orientation;
        this.width = data.width * 100;
        this.color = data.color;
    }

    AddToScene() {
        this.shape = new Two.Line(-this.width / 2, 0, this.width / 2, 0);
        this.shape.rotation = this.orientation * Math.PI / 180;
        this.body = this.two.makeGroup(this.shape);
        this.body.translation = this.position;
        this.body.linewidth = 20;
        this.body.stroke = LIGHT_COLORS[this.color]
        this.two.add(this.body);
    }

    Update(color) { //Color green = 1, amber = 2, red = 3
        this.color = color;
        this.body.stroke = LIGHT_COLORS[color];
    }
}

export class Connection extends MapObject {
    constructor(data, two) {
        super(data, two);
        this.points = data.points;
        this.width = data.width * 100;
    }

    AddToScene() {
        let anchors = [];
        this.points.forEach(p => {
            let x = p.x * 100;
            let y = p.y * 100;
            anchors.push(new Two.Anchor(x, y, x, y, x, y));
        });
        this.path = new Two.Path(anchors, false, false);
        this.path.stroke = "#444444";
        this.path.fill = "transparent";
        this.path.opacity = 0.2
        this.path.linewidth = 5;//this.width;
        this.two.add(this.path);
    }
}
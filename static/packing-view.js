/* Canvas projection only renders data produced by Python; it performs no packing. */
(() => {
  const canvas = document.querySelector("#packing-canvas");
  if (!canvas || !window.CanvasRenderingContext2D) return;
  const packing = JSON.parse(
    document.querySelector("#packing-data").textContent,
  );
  const box = JSON.parse(document.querySelector("#box-data").textContent);
  const context = canvas.getContext("2d");
  let rotation = -0.65,
    tilt = 0.48,
    zoom = 1,
    baseScale = 1,
    dragging = false,
    point = null;
  const dimensions = [
    Number(box.length),
    Number(box.width),
    Number(box.height),
  ];
  const colors = [
    "#51c39a",
    "#7aa7ff",
    "#e6b56d",
    "#d482c3",
    "#6ed5d3",
    "#ef8c7c",
  ];
  const project = ([x, y, z]) => {
    const c = Math.cos(rotation),
      s = Math.sin(rotation),
      ct = Math.cos(tilt),
      st = Math.sin(tilt);
    const rx = x * c - y * s,
      ry = x * s + y * c;
    return [
      canvas.width / 2 + rx * 1.05 * baseScale * zoom,
      canvas.height * 0.62 + (ry * st - z * ct) * baseScale * zoom,
    ];
  };
  const drawCuboid = (origin, dims, color, alpha) => {
    const [x, y, z] = origin,
      [l, w, h] = dims;
    const vertices = [
      [x, y, z],
      [x + l, y, z],
      [x + l, y + w, z],
      [x, y + w, z],
      [x, y, z + h],
      [x + l, y, z + h],
      [x + l, y + w, z + h],
      [x, y + w, z + h],
    ].map(project);
    const faces = [
      [0, 1, 2, 3],
      [0, 1, 5, 4],
      [1, 2, 6, 5],
      [2, 3, 7, 6],
      [3, 0, 4, 7],
      [4, 5, 6, 7],
    ];
    faces.forEach((face, index) => {
      context.beginPath();
      face.forEach((v, pos) =>
        pos ? context.lineTo(...vertices[v]) : context.moveTo(...vertices[v]),
      );
      context.closePath();
      context.fillStyle = `${color}${Math.round(
        alpha * (index === 5 ? 1 : 0.72),
      )
        .toString(16)
        .padStart(2, "0")}`;
      context.fill();
      context.strokeStyle = color;
      context.stroke();
    });
  };
  const draw = () => {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    context.lineWidth = devicePixelRatio;
    context.clearRect(0, 0, canvas.width, canvas.height);
    baseScale = Math.min(
      (canvas.width / (dimensions[0] + dimensions[1])) * 0.65,
      (canvas.height / (dimensions[1] + dimensions[2])) * 0.65,
    );
    drawCuboid([0, 0, 0], dimensions, "#5f8f9b", 10);
    packing.placements.forEach((placement, index) =>
      drawCuboid(
        [Number(placement.x), Number(placement.y), Number(placement.z)],
        placement.dimensions.map(Number),
        colors[index % colors.length],
        95,
      ),
    );
  };
  canvas.addEventListener("pointerdown", (e) => {
    dragging = true;
    point = [e.clientX, e.clientY];
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    rotation += (e.clientX - point[0]) * 0.01;
    tilt = Math.max(0.12, Math.min(1.2, tilt + (e.clientY - point[1]) * 0.01));
    point = [e.clientX, e.clientY];
    draw();
  });
  canvas.addEventListener("pointerup", () => (dragging = false));
  canvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      zoom *= e.deltaY > 0 ? 0.9 : 1.1;
      draw();
    },
    { passive: false },
  );
  window.addEventListener("resize", draw);
  draw();
})();

const input = document.getElementById("contrasena");

const requisitos = {
  length: document.getElementById("val-length"),
  mayus: document.getElementById("val-mayus"),
  minus: document.getElementById("val-minus"),
  num: document.getElementById("val-num"),
  especial: document.getElementById("val-especial"),
  espacios: document.getElementById("val-espacios")
};

const actualizarEstado = (elemento, valido) => {
  const icono = elemento.querySelector("i");

  if (valido) {
    icono.className = "bi bi-check-circle-fill text-success fs-5";
    elemento.classList.remove("text-danger", "fw-semibold");
    elemento.classList.add("text-success", "fw-semibold");
  } else {
    icono.className = "bi bi-x-circle-fill text-danger fs-5";
    elemento.classList.remove("text-success");
    elemento.classList.add("text-danger", "fw-semibold");
  }
};

input.addEventListener("input", () => {
  const val = input.value;

  actualizarEstado(requisitos.length, val.length >= 8);
  actualizarEstado(requisitos.mayus, /[A-Z]/.test(val));
  actualizarEstado(requisitos.minus, /[a-z]/.test(val));
  actualizarEstado(requisitos.num, /\d/.test(val));
  actualizarEstado(requisitos.especial, /[!@#$%^&*(),.?":{}|<>_\-+=;]/.test(val));
  actualizarEstado(requisitos.espacios, !/\s/.test(val));

  // Revalidar coincidencia en tiempo real también
  if (typeof validarCoincidencia === "function") {
    validarCoincidencia();
  }
});

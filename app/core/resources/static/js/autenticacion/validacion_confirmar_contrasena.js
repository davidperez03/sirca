const confirmar = document.getElementById("confirmar_contrasena");
const mensajeConfirmacion = document.getElementById("mensaje-confirmacion");
const botonRegistrar = document.querySelector("form button[type=submit]");

function validarCoincidencia() {
  const iguales = input.value === confirmar.value && input.value.length > 0;

  if (iguales) {
    mensajeConfirmacion.classList.add("d-none");
    confirmar.classList.remove("is-invalid");
    confirmar.classList.add("is-valid");
  } else {
    mensajeConfirmacion.classList.remove("d-none");
    confirmar.classList.remove("is-valid");
    confirmar.classList.add("is-invalid");
  }

  const requisitosOk = document.querySelectorAll("#requisitos-contrasena .bi-check-circle-fill").length === 6;
  botonRegistrar.disabled = !iguales || !requisitosOk;
}

confirmar.addEventListener("input", validarCoincidencia);

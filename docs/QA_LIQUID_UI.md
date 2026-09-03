# QA — Rediseño Liquid UI (Formulario + Panel Admin)

Checklist de control de calidad y criterios de aceptación para el rediseño
minimalista + Liquid UI. No se modificó la lógica funcional ni el backend;
solo interfaz y microinteracciones de presentación.

---

## 1. Funcional (no debe haberse roto)

- [ ] `POST /api/respostas` sigue funcionando (enviar formulario guarda datos).
- [ ] Validación estricta del cliente sigue activa (config `REGLAS` intacta).
- [ ] Sanitización anti-XSS intacta (`escapeHTML`/`normalizar`).
- [ ] Panel admin carga en `/admin-<TOKEN>` (HTML servido por backend).
- [ ] Listado, detalle (descifrado) y exportación Excel del panel funcionan.
- [ ] Filtros por cargo y universidad del panel funcionan.
- [ ] Token inválido sigue devolviendo 404 (secreto de URL intacto).
- [ ] Botón "Sair" del panel vuelve a `/`.

## 2. Reglas de diseño (no negociables)

- [ ] Textos visibles en **portugués**; atributos técnicos/clases en **español**.
- [ ] IDs/names de los campos no cambiaron (integridad del backend/convención).
- [ ] Mucho espacio en blanco; tipografía **Inter** con fallback a sistema.
- [ ] Radios orgánicos 12–18px; algunos contenedores pill (`9999px`).
- [ ] Degradados sutiles; `backdrop-filter` blur en tarjetas/stepper.
- [ ] Morphing en pasos (stepper) y botones (hover/active/shine).
- [ ] Hero con overlay blur; sin texto dentro de imágenes.

## 3. Microinteracciones

- [ ] Stepper indica la sección activa según el scroll (IntersectionObserver).
- [ ] Clic en un paso desplaza suave a la sección correspondiente.
- [ ] Botón enviar: morphing hover (elevación + brillo), active scale.
- [ ] Botón enviar muestra spinner interno durante el envío.
- [ ] Estado loading/exito/error aparece con animación de entrada.
- [ ] Campos inválidos vibran (`agitar`) y muestran borde/sombra roja.
- [ ] Los campos limpian el error al volver a escribir.

## 4. Accesibilidad (WCAG AA)

- [ ] Contrastes de texto cumplen AA (azules oscuros sobre fondo claro, blanco sobre azul).
- [ ] `label` vinculados a sus inputs (`for`/`id`).
- [ ] `focus-visible` visible en inputs y botones (foco de 3px + offset).
- [ ] Tamaños táctiles ≥ 40px en botones/controles interactivos.
- [ ] `prefers-reduced-motion` desactiva animaciones/transiciones.
- [ ] Estado con `role="status"` y `aria-live="polite"` (sin cambios).
- [ ] Stepper usa `aria-label` de progreso.

## 5. Responsivo

- [ ] Formulario usable en móvil (container 100%, padding reducido).
- [ ] Panel: header y `.acoes` se apilan en pantallas pequeñas.
- [ ] Tabla con scroll horizontal (`overflow-x`) en móvil.
- [ ] Stepper hace wrap y reduce su radio en móvil.

## 6. Criterios de aceptación

- [ ] El formulario se ve minimalista y moderno (Liquid), no rompe al enviar.
- [ ] El panel admin conserva funcionalidad y se ve coherente con el token.
- [ ] No hay imágenes con texto sobrepuesto.
- [ ] Los tests del backend siguen en verde (regresión funcional = 0).
- [ ] Sin cambios de lógica: solo CSS, HTML (clases nav/meta) y JS de UI.

---
## 7. Integración Pico.css (CSS-only autohospedada)

- [ ] `pico.min.css` (Pico 2.0.6) autohospedado en la raíz; se sirve en `'self'` (no depende de CDN; respeta `style-src 'self'`).
- [ ] Se carga ANTES que el CSS custom (`style.css` / `porphyria.css`) en `index.html` y `panel_admin.html`.
- [ ] Las clases custom (`.entrada`, `.campo`, `.boton-enviar`) tienen especificidad de clase y siguen ganando sobre las primitives de Pico (sin regresión visual en el formulario).
- [ ] El tema de Pico está alineado con los tokens Liquid (azul `#1E40AF`) vía variables `--pico-primary*` en `style.css`.
- [ ] `prefers-reduced-motion` sigue desactivando animaciones de Pico (heredado del CSS global).

---
## 8. Obra de arte glassmórfica (capa visual, sin tocar lógica)

- [ ] Fondo orgánico animado: blobs (`body::before/::after`) con `border-radius` asimétrico orgánico, `filter: blur`, que respiran y rotan (`@keyframes blob_float_*`).
- [ ] Escena `#escena-fondo` con orbes `<i>` flotantes (CSS puro, aria-hidden, inline styles permitidos por CSP).
- [ ] Glassmorfismo real en tarjetas (`.glass`, `.espaciado-formulario`, `.contenedor-formulario`, header/filtros/tabla del panel): `backdrop-filter: blur + saturate`, borde `rgba(255,255,255,.6)`, sombra interior + exterior.
- [ ] Contraste de fondo con la interacción: `:focus-within` enciende el aura del formulario y acelera los blobs (`body:has(:focus-within)::before/::after`).
- [ ] Formas orgánicas: `--radius-org` (blob), `conic-gradient` halo que gira en el encabezado, píldoras.
- [ ] Botón enviar: gradiente animado (`boton_grad`) + sheen que barre (`sheen`), pill morphing.
- [ ] Confeti líquido `.estallido` en `celebrar()` (partículas con `--dx/--dy`).
- [ ] `prefers-reduced-motion` sigue desactivando todas las animaciones (accesibilidad).
- [ ] Pico.css + primitives alineados; sin scripts externos (CSP `script-src 'self'` intacta).

---

## Verificación recomendada

```bash
# Regresión funcional del backend (no debe fallar nada)
cd backend
python -m pytest

# Abrir en navegador
#   - index.html                 (formulario)
#   - /admin-<ADMIN_TOKEN>        (panel admin, servido por el backend)
```

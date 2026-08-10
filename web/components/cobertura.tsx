"use client";

import { Modal } from "@/components/ui/modal";

// Fecha de corte del corpus. Se actualiza a mano cada vez que se reindexa:
// una fecha automática diría "hoy" aunque los documentos fueran de hace meses.
const ACTUALIZADO_AL = "10 de agosto de 2026";

// Las fuentes se agrupan por rango, no por tema: una circular del MINVU o un
// manual ilustrado no tienen la misma fuerza que una ley, y mostrarlos en una
// sola lista plana sugiere lo contrario.
const COBERTURA = [
  {
    titulo: "Normativa vigente",
    nota: "Texto con fuerza obligatoria.",
    docs: [
      [
        "LGUC",
        "Ley General de Urbanismo y Construcciones (DFL 458). Texto vigente desde el 24 de junio de 2026.",
      ],
      [
        "OGUC",
        "Ordenanza General de Urbanismo y Construcciones (DS 47). Actualizada a marzo de 2026.",
      ],
      [
        "Ley N° 21.442",
        "Copropiedad Inmobiliaria. Versión vigente al 16 de febrero de 2026.",
      ],
      [
        "Reglamento de la Ley N° 21.442",
        "Desarrolla asambleas, administración, bienes comunes y registros. Publicado el 9 de enero de 2025.",
      ],
      [
        "Ley N° 21.807",
        "Fortalece y moderniza el sistema de planificación territorial. Publicada el 16 de febrero de 2026.",
      ],
      ["DS 50", "Accesibilidad Universal (2015), incorporado a la OGUC."],
    ],
  },
  {
    titulo: "Interpretación oficial",
    nota: "Instruye cómo aplicar la norma; no la reemplaza.",
    docs: [
      [
        "Circulares DDU",
        "250 circulares generales vigentes del MINVU, hasta la DDU 548. De ellas, 42 son escaneos antiguos sin texto extraíble y no participan en la búsqueda.",
      ],
    ],
  },
  {
    titulo: "Procedimiento y formularios",
    nota: "Antecedentes que exige cada trámite ante la Dirección de Obras Municipales.",
    docs: [
      [
        "Formularios Únicos Nacionales",
        "57 formularios del MINVU: anteproyecto, permiso de edificación, modificación de proyecto y recepción definitiva.",
      ],
    ],
  },
  {
    titulo: "Material explicativo",
    nota: "No es norma y nunca reemplaza la cita al texto oficial.",
    docs: [
      [
        "OGUC Ilustrada, tomos I y II",
        "Manual con esquemas y diagramas, incorporado mediante descripción visual de cada página.",
      ],
    ],
  },
] as const;

const NO_INCLUYE = [
  "Planes reguladores comunales, intercomunales y metropolitanos",
  "Normas chilenas NCh de referencia obligatoria",
  "Dictámenes de la Contraloría General de la República",
  "Listados técnicos DITEC de fuego, térmico y acústico",
  "Jurisprudencia judicial y administrativa",
] as const;

/** Qué normativa cubre Norma y cuál no. Se abre desde la barra lateral y
 *  desde el composer: una sola lista para no arriesgar que diverjan. */
export function CoberturaModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Modal title="Cobertura y fuentes" open={open} onClose={onClose}>
      <p>
        Norma responde únicamente con los documentos de esta lista. No consulta
        internet ni ninguna otra fuente.
      </p>
      <p className="mt-2 text-[13px] text-text-subtle">
        Actualizado al {ACTUALIZADO_AL}.
      </p>

      {COBERTURA.map((grupo) => (
        <section key={grupo.titulo} className="mt-5">
          <h3 className="text-[13px] font-medium uppercase tracking-wide text-text-primary">
            {grupo.titulo}
          </h3>
          <p className="mt-0.5 text-[13px] text-text-subtle">{grupo.nota}</p>
          <ul className="mt-2 space-y-2">
            {grupo.docs.map(([nombre, detalle]) => (
              <li key={nombre}>
                <span className="font-medium text-text-primary">{nombre}</span>
                <span> — {detalle}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <section className="mt-5 border-t border-line-subtle pt-4">
        <h3 className="text-[13px] font-medium uppercase tracking-wide text-text-primary">
          Aún no incluye
        </h3>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {NO_INCLUYE.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p className="mt-3 text-[13px] text-text-subtle">
          Si tu consulta depende de alguno de estos, verifícala directamente con
          la Dirección de Obras Municipales.
        </p>
      </section>
    </Modal>
  );
}

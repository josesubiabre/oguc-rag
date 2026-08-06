"use client";

import { Modal } from "@/components/ui/modal";

interface LegalDisclaimerModalProps {
  open: boolean;
  onClose: () => void;
}

/** Aviso legal de NormaObra. Contenido único, invocable desde varios puntos. */
export function LegalDisclaimerModal({ open, onClose }: LegalDisclaimerModalProps) {
  return (
    <Modal title="Aviso legal" open={open} onClose={onClose}>
      <div className="space-y-3">
        <p>
          <span className="font-medium text-text-primary">
            Carácter informativo.
          </span>{" "}
          NormaObra es una herramienta de consulta informativa. Sus respuestas
          no constituyen asesoría legal, técnica ni profesional, y no
          reemplazan la revisión de la normativa vigente ni el juicio de un
          profesional competente (arquitecto, abogado o revisor independiente,
          según corresponda).
        </p>
        <p>
          <span className="font-medium text-text-primary">
            Contenido generado por inteligencia artificial.
          </span>{" "}
          Las respuestas se generan automáticamente a partir de fragmentos de
          la normativa indexada y pueden contener errores, omisiones o
          interpretaciones imprecisas. En caso de discrepancia, prevalece
          siempre el texto oficial publicado en el Diario Oficial y en los
          sitios del MINVU.
        </p>
        <p>
          <span className="font-medium text-text-primary">
            Sin afiliación oficial.
          </span>{" "}
          NormaObra no tiene relación con el Ministerio de Vivienda y
          Urbanismo ni con ningún organismo del Estado de Chile. Los textos
          normativos citados son de acceso público.
        </p>
        <p>
          <span className="font-medium text-text-primary">
            Responsabilidad.
          </span>{" "}
          El uso de esta herramienta es bajo tu propio riesgo. No asumimos
          responsabilidad por decisiones, trámites, proyectos o pérdidas
          derivadas del uso de las respuestas entregadas.
        </p>
        <p>
          <span className="font-medium text-text-primary">Privacidad.</span>{" "}
          Las preguntas se procesan mediante servicios externos de inteligencia
          artificial para generar la respuesta. No ingreses datos personales,
          confidenciales o de terceros. El historial de conversaciones se
          guarda únicamente en tu navegador y puedes borrarlo limpiando los
          datos del sitio.
        </p>
      </div>
    </Modal>
  );
}

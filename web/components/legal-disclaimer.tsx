"use client";

import { Modal } from "@/components/ui/modal";

/** Aviso breve que acompaña cada respuesta generada. */
export const SHORT_DISCLAIMER =
  "NormaObra utiliza inteligencia artificial y puede cometer errores. " +
  "Verifica siempre la norma citada, su vigencia y su aplicación al caso " +
  "concreto. No reemplaza la revisión de un profesional competente ni el " +
  "criterio de la autoridad correspondiente.";

interface LegalDisclaimerModalProps {
  open: boolean;
  onClose: () => void;
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2">
      <h3 className="font-medium text-text-primary">{title}</h3>
      {children}
    </section>
  );
}

/** Aviso de uso y limitaciones de NormaObra. */
export function LegalDisclaimerModal({ open, onClose }: LegalDisclaimerModalProps) {
  return (
    <Modal title="Aviso de uso y limitaciones" open={open} onClose={onClose}>
      <div className="space-y-4">
        <p className="text-[13px] text-text-subtle">
          Última actualización: 6 de agosto de 2026
        </p>

        <Section title="Herramienta de información y consulta">
          <p>
            NormaObra facilita la búsqueda y comprensión de normativa
            relacionada con urbanismo y construcción en Chile. La información
            entregada tiene carácter general e informativo y no constituye
            asesoría legal, arquitectónica, de ingeniería, técnica ni
            profesional. Tampoco certifica el cumplimiento normativo, la
            factibilidad de un proyecto ni la obtención de permisos o
            autorizaciones.
          </p>
        </Section>

        <Section title="Contenido generado mediante inteligencia artificial">
          <p>
            Las respuestas se generan automáticamente a partir de documentos y
            fragmentos normativos indexados. Aunque NormaObra procura
            identificar y citar fuentes relevantes, las respuestas pueden
            contener errores, omisiones, referencias desactualizadas o
            interpretaciones incorrectas. Una cita correcta tampoco garantiza
            que la conclusión sea aplicable al caso consultado.
          </p>
        </Section>

        <Section title="Fuentes y vigencia">
          <p>
            La normativa puede ser modificada, reemplazada, derogada o quedar
            sujeta a disposiciones transitorias. NormaObra no garantiza que
            todos los documentos aplicables ni sus modificaciones más
            recientes se encuentren incorporados al momento de cada consulta.
          </p>
          <p>
            Antes de utilizar una respuesta, debes revisar la disposición
            citada, su fecha de vigencia y su texto completo en las fuentes
            oficiales correspondientes. En caso de discrepancia, prevalecerá
            siempre el texto oficial vigente publicado o reconocido por la
            autoridad competente.
          </p>
        </Section>

        <Section title="Aplicación a casos concretos">
          <p>
            La normativa aplicable puede variar según la ubicación, destino,
            características y fecha de ingreso de un proyecto, así como por
            instrumentos de planificación territorial, ordenanzas locales,
            permisos, certificados, resoluciones y criterios de la autoridad
            competente.
          </p>
          <p>
            No utilices una respuesta de NormaObra como única base para
            preparar expedientes, realizar cálculos, adoptar decisiones de
            diseño, ejecutar obras, suscribir contratos o presentar
            solicitudes ante una autoridad. Para decisiones con consecuencias
            legales, técnicas o económicas, consulta a un profesional
            competente y, cuando corresponda, confirma el criterio con la
            Dirección de Obras Municipales u otra autoridad responsable.
          </p>
        </Section>

        <Section title="Sin afiliación oficial">
          <p>
            NormaObra es una herramienta independiente y no pertenece,
            representa ni está afiliada al Ministerio de Vivienda y Urbanismo,
            a las Direcciones de Obras Municipales ni a ningún otro organismo
            del Estado de Chile. Los nombres, documentos y referencias
            institucionales se utilizan únicamente para identificar las
            fuentes consultadas.
          </p>
        </Section>

        <Section title="Responsabilidad del usuario">
          <p>
            Eres responsable de verificar la información y de las decisiones
            que adoptes a partir de ella. En la máxima medida permitida por la
            legislación aplicable, NormaObra no será responsable por
            decisiones o actuaciones basadas exclusivamente en sus respuestas
            ni por consecuencias derivadas de información incorrecta,
            incompleta o desactualizada.
          </p>
          <p>
            Nada de lo señalado en este aviso limita derechos irrenunciables
            de los usuarios ni excluye responsabilidades que legalmente no
            puedan ser excluidas.
          </p>
        </Section>

        <Section title="Privacidad y datos personales">
          <p>
            Las consultas y ciertos datos técnicos necesarios para prestar y
            proteger el servicio pueden ser procesados por proveedores
            externos de infraestructura e inteligencia artificial. No ingreses
            datos personales sensibles, información confidencial, secretos
            comerciales ni datos de terceros que no estés autorizado a
            compartir.
          </p>
          <p>
            La identidad del responsable del tratamiento, las finalidades, los
            proveedores utilizados, los posibles flujos internacionales de
            datos, los períodos de conservación y la forma de ejercer tus
            derechos se informarán en la Política de Privacidad, actualmente
            en preparación.
          </p>
        </Section>

        <div className="border-t border-line-subtle pt-3 text-[13px]">
          {/* TODO: reemplazar por el nombre o razón social definitivos */}
          <p>
            <span className="text-text-primary">Responsable del servicio:</span>{" "}
            josesubiabre
          </p>
          <p>
            <span className="text-text-primary">Contacto:</span>{" "}
            subiabreji@gmail.com
          </p>
        </div>
      </div>
    </Modal>
  );
}

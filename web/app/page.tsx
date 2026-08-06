import { OgucChat } from "@/components/ui/oguc-chat";

export default function Page() {
  return (
    <main className="flex-1 flex flex-col items-center justify-start bg-neutral-950 pt-24 pb-8 px-4">
      <OgucChat />
      <p className="mt-auto pt-10 max-w-xl text-center text-[0.72rem] text-neutral-600">
        Herramienta informativa no oficial basada en la OGUC (marzo 2026).
        Verifica siempre con el texto vigente y un profesional competente.
      </p>
    </main>
  );
}

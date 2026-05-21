import { createContext } from 'react';

/** `undefined` = aún cargando; `null` = Google no configurado en el backend */
export const GoogleClientIdContext = createContext<string | null | undefined>(undefined);

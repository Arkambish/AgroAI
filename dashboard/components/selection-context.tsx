"use client";

import React, { createContext, useContext, useState } from "react";

type SelectionContextType = {
  district: string | null;
  setDistrict: (d: string) => void;
};

const SelectionContext = createContext<SelectionContextType | null>(null);

export function SelectionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [district, setDistrict] = useState<string | null>(null);

  return (
    <SelectionContext.Provider value={{ district, setDistrict }}>
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelection() {
  const ctx = useContext(SelectionContext);
  if (!ctx) throw new Error("useSelection must be used inside provider");
  return ctx;
}
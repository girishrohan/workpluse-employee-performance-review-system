"use client";

import { createContext, useContext } from "react";

const WorkspaceUserContext = createContext("");

export function WorkspaceUserProvider({ userId, children }: { userId: string; children: React.ReactNode }) {
  return <WorkspaceUserContext.Provider value={userId}>{children}</WorkspaceUserContext.Provider>;
}

export function useWorkspaceUserId() {
  return useContext(WorkspaceUserContext);
}

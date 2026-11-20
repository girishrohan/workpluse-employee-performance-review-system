"use client";

import { createContext, useContext } from "react";

interface WorkspaceUserContextValue {
  userId: string;
  role: string;
}

const WorkspaceUserContext = createContext<WorkspaceUserContextValue>({ userId: '', role: 'employee' });

export function WorkspaceUserProvider({ userId, role, children }: { userId: string; role: string; children: React.ReactNode }) {
  return <WorkspaceUserContext.Provider value={{ userId, role }}>{children}</WorkspaceUserContext.Provider>;
}

export function useWorkspaceUserId() {
  return useContext(WorkspaceUserContext).userId;
}

export function useWorkspaceRole() {
  return useContext(WorkspaceUserContext).role;
}

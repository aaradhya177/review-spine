"use client";
import { Check, MessageSquareWarning, X } from "lucide-react";
export function HitlActions() { return <div className="actions"><button className="button primary" type="button"><Check className="icon" />Approve</button><button className="button danger" type="button"><X className="icon" />Dismiss</button><button className="button" type="button"><MessageSquareWarning className="icon" />Escalate</button></div>; }

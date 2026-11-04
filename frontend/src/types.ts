// Types used only inside the frontend; what the server sends is described in protocol.ts

export interface AvatarOption {
  id: string;
  name: string;
  mood: string;
  tag: string;
  bgColor: string;
  accentColor: string;
}

export interface DirectoryTreeNode {
  name: string;
  children: DirectoryTreeNode[];
  file: string;
  parent: DirectoryTreeNode | null;
}

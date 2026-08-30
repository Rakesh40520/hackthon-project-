import { useDropzone } from "react-dropzone";
import { UploadCloud, FileText, X } from "lucide-react";
import clsx from "clsx";

export function Dropzone({
  onFile,
  accept = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "text/csv": [".csv"],
    "text/plain": [".txt"],
  },
  selected,
  onClear,
}: {
  onFile: (file: File) => void;
  accept?: any;
  selected?: File | null;
  onClear?: () => void;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => {
      if (files[0]) onFile(files[0]);
    },
    multiple: false,
    accept,
  });
  if (selected) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
          <FileText className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">{selected.name}</div>
          <div className="text-xs text-slate-500">{(selected.size / 1024 / 1024).toFixed(2)} MB</div>
        </div>
        {onClear ? (
          <button onClick={onClear} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500">
            <X className="w-4 h-4" />
          </button>
        ) : null}
      </div>
    );
  }
  return (
    <div
      {...getRootProps()}
      className={clsx(
        "rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition",
        isDragActive ? "border-accent-500 bg-accent-50" : "border-slate-200 bg-white hover:border-slate-300"
      )}
    >
      <input {...getInputProps()} />
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-500 mb-3">
        <UploadCloud className="w-6 h-6" />
      </div>
      <div className="text-sm font-medium text-slate-700">
        {isDragActive ? "Drop the file here" : "Drop vendor proposal here"}
      </div>
      <div className="text-xs text-slate-500 mt-1">or click to upload</div>
      <div className="mt-3 text-[10px] uppercase tracking-wider text-slate-400">PDF • DOCX • XLSX • CSV • TXT</div>
    </div>
  );
}

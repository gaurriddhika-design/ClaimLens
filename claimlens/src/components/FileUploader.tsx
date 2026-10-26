
import { useState } from 'react';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
}

export default function FileUploader({
  onFileSelect,
}: FileUploaderProps) {
  const [fileName, setFileName] = useState('');

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (file) {
      setFileName(file.name);
      onFileSelect(file);
    }
  };

  return (
    <div className="file-uploader">
      <label htmlFor="evidence-file">
        Upload Evidence
      </label>

      <input
        id="evidence-file"
        type="file"
        accept=".pdf,.txt,.png,.jpg,.jpeg"
        onChange={handleFileChange}
      />

      {fileName && (
        <p>Selected file: {fileName}</p>
      )}
    </div>
  );
}

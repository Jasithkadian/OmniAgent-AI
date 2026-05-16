import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Files, Upload, Loader2, CheckCircle2 } from 'lucide-react';
import { documentService } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

const DocumentUpload: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await documentService.upload(file);
      toast({
        title: "Upload Successful",
        description: `${file.name} has been queued for indexing.`,
      });
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: error.response?.data?.detail || "An unexpected error occurred.",
      });
    } finally {
      setIsUploading(false);
      // Reset input
      event.target.value = '';
    }
  };

  return (
    <div className="relative">
      <input
        type="file"
        id="file-upload"
        className="hidden"
        onChange={handleFileChange}
        accept=".pdf,.docx,.txt"
        disabled={isUploading}
      />
      <label htmlFor="file-upload">
        <Button 
          variant="secondary" 
          className="w-full justify-start gap-2 cursor-pointer shadow-sm"
          asChild
          disabled={isUploading}
        >
          <span>
            {isUploading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
            {isUploading ? 'Uploading...' : 'Upload Knowledge'}
          </span>
        </Button>
      </label>
    </div>
  );
};

export default DocumentUpload;

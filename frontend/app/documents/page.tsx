"use client";

import { useState } from "react";
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/lib/hooks";

interface Document {
  document_id: string;
  filename: string;
  size_mb: number;
  upload_time: string;
  file_type: string;
}

export default function DocumentsPage() {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");
  
  const { data: documents = [], isLoading } = useDocuments();
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();


  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    setError("");

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Validate file type
      const allowedTypes = [".pdf", ".txt", ".docx"];
      const fileExtension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
      if (!allowedTypes.includes(fileExtension)) {
        setError(`File type ${fileExtension} not allowed. Allowed types: ${allowedTypes.join(", ")}`);
        continue;
      }

      // Validate file size (100MB limit)
      if (file.size > 100 * 1024 * 1024) {
        setError(`File ${file.name} exceeds 100MB limit`);
        continue;
      }

      uploadMutation.mutate(file, {
        onError: (error) => {
          setError(error instanceof Error ? error.message : "Upload failed");
        },
      });
    }
  };

  const handleDelete = (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

    deleteMutation.mutate(documentId, {
      onError: (error) => {
        console.error("Failed to delete document:", error);
      },
    });
  };

  return (
    <div className="px-4 py-5 sm:px-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Document Management</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload and manage your confidential legal documents
        </p>
      </div>

      {/* Upload Area */}
      <div className="mb-8">
        <div
          className={`relative border-2 border-dashed rounded-lg p-6 ${
            dragActive ? "border-indigo-500 bg-indigo-50" : "border-gray-300"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              {uploadMutation.isPending ? (
                "Uploading..."
              ) : (
                <>
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-indigo-600 hover:text-indigo-500">
                      Click to upload
                    </span>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      className="sr-only"
                      multiple
                      accept=".pdf,.txt,.docx"
                      onChange={handleChange}
                      disabled={uploadMutation.isPending}
                    />
                  </label>
                  <span> or drag and drop</span>
                </>
              )}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              PDF, TXT, DOCX up to 100MB
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-2 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Uploaded Documents</h3>
        {isLoading ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">No documents uploaded yet</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <li key={doc.document_id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <span className="text-2xl">
                          {doc.file_type === ".pdf" ? "📄" : doc.file_type === ".docx" ? "📝" : "📃"}
                        </span>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-sm text-gray-500">
                          {doc.size_mb} MB • Uploaded {new Date(doc.upload_time).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.document_id, doc.filename)}
                      disabled={deleteMutation.isPending}
                      className="text-red-600 hover:text-red-900 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deleteMutation.isPending ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Storage Info */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              <strong>Storage Notice:</strong> All documents are stored in temporary memory (tmpfs) only.
              They will be permanently deleted when your session ends.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
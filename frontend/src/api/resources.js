import api from "./client";

export const authApi = {
  signup: (payload) => api.post("/api/auth/signup", payload),
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return api.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  verifyEmail: (token) => api.post("/api/auth/verify-email", { token }),
  resendVerification: (email) => api.post("/api/auth/resend-verification", { email }),
  forgotPassword: (email) => api.post("/api/auth/forgot-password", { email }),
  resetPassword: (token, newPassword) =>
    api.post("/api/auth/reset-password", { token, new_password: newPassword }),
};

export const resumeApi = {
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/api/resumes/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: () => api.get("/api/resumes/"),
  get: (id) => api.get(`/api/resumes/${id}`),
  remove: (id) => api.delete(`/api/resumes/${id}`),
  analyze: (id, jobDescription, jobRole) =>
    api.post(`/api/resumes/${id}/analyze`, {
      job_description: jobDescription || null,
      job_role: jobRole || null,
    }),
  downloadReport: (resumeId, analysisId) =>
    api.get(`/api/resumes/${resumeId}/analyses/${analysisId}/report`, { responseType: "blob" }),
  tailor: (id, jobDescription, jobRole, extraSkills) =>
    api.post(
      `/api/resumes/${id}/tailor`,
      {
        job_description: jobDescription || null,
        job_role: jobRole || null,
        extra_skills: extraSkills || null,
      },
      { responseType: "blob" }
    ),
};

export const jobsApi = {
  search: (q, location, country = "in", page = 1) =>
    api.get("/api/jobs/search", { params: { q, location, country, page } }),
};

import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the api module used by documentService
const mockPost = vi.fn();
vi.mock('../../services/api', () => ({
  api: {
    post: (...args: any[]) => mockPost(...args),
  },
}));

import { getPresignedUrl } from '../../services/documentService';

describe('documentService.getPresignedUrl', () => {
  beforeEach(() => {
    mockPost.mockReset();
  });

  it('posts filename and contentType in JSON body', async () => {
    mockPost.mockResolvedValue({ data: { uploadUrl: 'u', uploadId: 'id' } });

    const filename = 'doc.pdf';
    const contentType = 'application/pdf';

    const resp = await getPresignedUrl(filename, contentType);

    expect(mockPost).toHaveBeenCalledTimes(1);
    expect(mockPost).toHaveBeenCalledWith('/document/presign', {
      filename,
      contentType,
    });

    expect(resp).toEqual({ uploadUrl: 'u', uploadId: 'id' });
  });
});

import { STORAGE_USERINFO_KEY } from '@/utils/constants/index';

const useUser = () => {
  try {
    const raw = localStorage.getItem(STORAGE_USERINFO_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export default useUser;

import { Outlet } from 'react-router';
import { Toaster } from 'react-hot-toast';

import { CookiesProvider } from '@/contexts/CookiesContext';
import { ZonesAndFspMapContextProvider } from '@/contexts/ZonesAndFspMapContext';
import { FileBrowserContextProvider } from '@/contexts/FileBrowserContext';
import { PreferencesProvider } from '@/contexts/PreferencesContext';
import { ProxiedPathProvider } from '@/contexts/ProxiedPathContext';
import FileglancerNavbar from '@/components/ui/Navbar';

export const MainLayout = () => {
  return (
    <CookiesProvider>
      <ZonesAndFspMapContextProvider>
        <PreferencesProvider>
          <FileBrowserContextProvider>
            <ProxiedPathProvider>
              <Toaster
                position="bottom-center"
                toastOptions={{
                  className: 'min-w-fit',
                  success: { duration: 4000 }
                }}
              />
              <div className="flex flex-col items-center h-full w-full overflow-y-hidden bg-background text-foreground box-border">
                <FileglancerNavbar />
                <Outlet />
              </div>
            </ProxiedPathProvider>
          </FileBrowserContextProvider>
        </PreferencesProvider>
      </ZonesAndFspMapContextProvider>
    </CookiesProvider>
  );
};

import { ModelSvg } from '@/components/icons';
import Icon, {
  AppstoreOutlined,
  BuildOutlined,
  ConsoleSqlOutlined,
  ForkOutlined,
  MessageOutlined,
  PartitionOutlined,
} from '@ant-design/icons';
import { ConfigProvider, Result, Tabs, Button } from 'antd';
import { t } from 'i18next';
import { useRouter } from 'next/router';
import React, { useMemo } from 'react';
import { STORAGE_UI_ADMIN_KEY } from '@/utils/constants/index';
import './style.css';

function ConstructLayout({ children }: { children: React.ReactNode }) {
  const hasAccess = useMemo(() => {
    try {
      const raw = localStorage.getItem(STORAGE_UI_ADMIN_KEY) || '';
      const parsed = raw ? JSON.parse(raw) : null;
      return parsed?.state?.isUIAdmin === true;
    } catch {
      return false;
    }
  }, []);
  const items = [
    {
      key: 'app',
      name: t('App'),
      path: '/app',
      icon: <AppstoreOutlined />,
      // operations: (
      //   <Button
      //     className='border-none text-white bg-button-gradient h-full flex items-center'
      //     icon={<PlusOutlined className='text-base' />}
      //     // onClick={handleCreate}
      //   >
      //     {t('create_app')}
      //   </Button>
      // ),
    },
    {
      key: 'flow',
      name: t('awel_flow'),
      icon: <ForkOutlined />,
      path: '/flow',
    },
    {
      key: 'models',
      name: t('model_manage'),
      path: '/models',
      icon: <Icon component={ModelSvg} />,
    },
    {
      key: 'database',
      name: t('Database'),
      icon: <ConsoleSqlOutlined />,
      path: '/database',
    },
    {
      key: 'knowledge',
      name: t('Knowledge_Space'),
      icon: <PartitionOutlined />,
      path: '/knowledge',
    },
    // {
    //   key: 'agent',
    //   name: t('Plugins'),
    //   path: '/agent',
    //   icon: <BuildOutlined />,
    // },
    {
      key: 'prompt',
      name: t('Prompt'),
      icon: <MessageOutlined />,
      path: '/prompt',
    },
    {
      key: 'dbgpts',
      name: t('dbgpts_community'),
      path: '/dbgpts',
      icon: <BuildOutlined />,
    },
  ];
  const router = useRouter();
  const activeKey = router.pathname.split('/')[2];
  // const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches; // unused

  if (!hasAccess) {
    return (
      <div className='flex flex-col h-full w-full dark:bg-gradient-dark bg-gradient-light bg-cover bg-center'>
        <ConfigProvider>
          <Result
            status='403'
            title='403'
            subTitle={'Only admins can access Construct'}
            extra={
              <Button type='primary' onClick={() => router.replace('/')}> 
                {'Back Home'}
              </Button>
            }
          />
        </ConfigProvider>
      </div>
    );
  }

  return (
    <div className='flex flex-col h-full w-full  dark:bg-gradient-dark bg-gradient-light bg-cover bg-center'>
      <ConfigProvider
        theme={{
          components: {
            Button: {
              // defaultBorderColor: 'white',
            },
            Segmented: {
              itemSelectedBg: '#2867f5',
              itemSelectedColor: 'white',
            },
          },
        }}
      >
        <Tabs
          // tabBarStyle={{
          //   background: '#edf8fb',
          //   border: 'none',
          //   height: '3.5rem',
          //   padding: '0 1.5rem',
          //   color: !isDarkMode ? 'white' : 'black',
          // }}
          activeKey={activeKey}
          items={items.map(items => {
            return {
              key: items.key,
              label: items.name,
              children: children,
              icon: items.icon,
            };
          })}
          onTabClick={key => {
            router.push(`/construct/${key}`);
          }}
          // tabBarExtraContent={
          //   <Button
          //     className='border-none text-white bg-button-gradient h-full flex items-center'
          //     icon={<PlusOutlined className='text-base' />}
          //     // onClick={handleCreate}
          //   >
          //     {t('create_app')}
          //   </Button>
          // }
        />
      </ConfigProvider>
    </div>
  );
}

export default ConstructLayout;

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
import React from 'react';
import useUser from '@/hooks/use-user';
import { useContext, useMemo, useEffect } from 'react';
import { ChatContext } from '@/app/chat-context';
import { STORAGE_USERINFO_KEY } from '@/utils/constants/index';
import './style.css';

function ConstructLayout({ children }: { children: React.ReactNode }) {
  const user = useUser() as any;
  const { adminList } = useContext(ChatContext);
  const hasAccess = useMemo(() => {
    try {
      const { user_id } = JSON.parse(localStorage.getItem(STORAGE_USERINFO_KEY) || '{}');
      if (!user_id) return false;
      const envAllow = (process.env.NEXT_PUBLIC_CONSTRUCT_ALLOWED_USER_IDS || '')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
      return (
        adminList.some((admin: any) => admin.user_id === user_id) ||
        envAllow.includes(user_id)
      );
    } catch {
      return false;
    }
  }, [adminList]);
  // Build tab items: always expose Database and Knowledge; other tabs only for admins/allowed users
  const items = useMemo(() => {
    const base = [
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
    ];
    if (hasAccess) {
      base.unshift(
        {
          key: 'app',
          name: t('App'),
          path: '/app',
          icon: <AppstoreOutlined />,
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
      );
      base.push(
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
      );
    }
    return base;
  }, [hasAccess]);
  const router = useRouter();
  const activeKey = router.pathname.split('/')[2];
  // const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches; // unused
  // If user opens a restricted tab directly, redirect to the first allowed tab
  useEffect(() => {
    const keys = items.map(i => i.key);
    if (!keys.includes(activeKey)) {
      // default to database for non-admins
      router.replace('/construct/' + keys[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeKey, items.length]);

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


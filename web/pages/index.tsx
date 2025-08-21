import { apiInterceptors, collectApp, getAppList, newDialogue, recommendApps, unCollectApp } from '@/client/api';
import { StarFilled, StarOutlined } from '@ant-design/icons';
import { useRequest } from 'ahooks';
// import type { SegmentedProps } from 'antd';
import { Avatar, ConfigProvider, Spin, message } from 'antd';
// import cls from 'classnames';
import { NextPage } from 'next';
import { useRouter } from 'next/router';
import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { GridCellRenderer, Index, IndexRange } from 'react-virtualized';
import { AutoSizer, Grid, InfiniteLoader } from 'react-virtualized';

import { ChatContext } from '@/app/chat-context';
import IconFont from '@/new-components/common/Icon';
import BlurredCard from '@/new-components/common/blurredCard';
import { AppListResponse } from '@/types/app';
import moment from 'moment';

const Playground: NextPage = () => {
  const router = useRouter();
  const { t } = useTranslation();
  const { setAgent, setCurrentDialogInfo, model } = useContext(ChatContext);

  // const [activeKey, setActiveKey] = useState<string>('all');
  const activeKey = 'all';
  const [apps, setApps] = useState<any>({
    app_list: [],
    total_count: 0,
  });

  // const items: SegmentedProps['options'] = [
  //   {
  //     value: 'recommend',
  //     label: t('recommend_apps'),
  //   },
  //   {
  //     value: 'all',
  //     label: t('all_apps'),
  //   },
  //   {
  //     value: 'collected',
  //     label: t('my_collected_apps'),
  //   },
  // ];

  const getAppListWithParams = (params: Record<string, string>) =>
    apiInterceptors(
      getAppList({
        page: '1',
        page_size: '12',
        ...params,
      }),
    );
  const getHotAppList = (params: Record<string, string>) =>
    apiInterceptors(
      recommendApps({
        page_no: '1',
        page_size: '12',
        ...params,
      }),
    );
  // Get the application list
  const { run: getAppListFn, loading } = useRequest(
    async (app_name = '', page_no = '1', page_size = '12') => {
      switch (activeKey) {
        case 'recommend':
          return await getHotAppList({
            ...{ page_no, page_size },
          });
        case 'collected':
          return await getAppListWithParams({
            is_collected: 'true',
            ignore_user: 'true',
            published: 'true',
            need_owner_info: 'true',
            ...{ app_name, page: page_no, page_size },
          });
        case 'all':
          return await getAppListWithParams({
            ignore_user: 'true',
            published: 'true',
            need_owner_info: 'true',

            ...{ app_name, page: page_no, page_size },
          });
        default:
          return [];
      }
    },
    {
      manual: true,
      onSuccess: (res: [any, [] | AppListResponse]) => {
        const [_error, data] = res;
        if (activeKey === 'recommend') {
          if (Array.isArray(data)) {
            return setApps({
              app_list: data,
              total_count: data.length,
            });
          }
        } else {
          // Ensure data is a non-null object before using the 'in' operator
          if (data && typeof data === 'object' && 'app_list' in data) {
            // Merge uniquely by app_code to avoid duplicates and support pagination reliably
            setApps(prev => {
              const prevList = prev.app_list || [];
              const existingIndexMap = new Map<string, number>();
              prevList.forEach((it: any, idx: number) => existingIndexMap.set(it.app_code, idx));
              const nextList = [...prevList];
              (data?.app_list || []).forEach((it: any) => {
                const existIdx = existingIndexMap.get(it.app_code);
                if (existIdx === undefined) {
                  nextList.push(it);
                } else {
                  nextList[existIdx] = it; // update in place
                }
              });
              return {
                app_list: nextList,
                total_count: (data as AppListResponse)?.total_count || prev.total_count || nextList.length,
              } as any;
            });
          }
        }
      },
      debounceWait: 500,
    },
  );

  // const onSearch = async (e: any) => {
  //   setApps({
  //     app_list: [],
  //     total_count: 0,
  //   });
  //   getAppListFn(e.target.value);
  // };

  const collect = async (data: Record<string, any>) => {
    const [error] = await apiInterceptors(
      data.is_collected === 'true'
        ? unCollectApp({ app_code: data.app_code })
        : collectApp({ app_code: data.app_code }),
    );
    const index = apps.app_list.findIndex((item: any) => item.app_code === data.app_code);
    if (error) return;
    if (data.is_collected === 'true') {
      message.success(t('cancel_success'));
    } else {
      message.success(t('collect_success'));
    }
    getAppListFn('', (Math.floor(index / 12) + 1).toString());
  };
  const columnCount = 3;

  function isRowLoaded({ index }: Index) {
    // Consider the row loaded only if the first item in the row exists
    const startItem = index * columnCount;
    return !!apps.app_list[startItem];
  }

  function loadMoreRows({ startIndex, stopIndex }: IndexRange) {
    // startIndex/stopIndex are ROW indices
    const pageSize = 12;
    const startItem = startIndex * columnCount;
    const currentPage = Math.floor(startItem / pageSize) + 1; // Calculate the current page based on item index
    console.log('loadMoreRows rowRange=', startIndex, stopIndex, 'startItem=', startItem, 'page=', currentPage);
    // This should be an asynchronous operation to get more data from the server
    // For example，You may call API and return one Promise
    return getAppListFn('', currentPage.toString());
  }
  const cellRenderer: GridCellRenderer = ({ columnIndex, key, rowIndex, style }) => {
    // Calculate the index in the array
    const index = rowIndex * columnCount + columnIndex;
    if (!isRowLoaded({ index: rowIndex })) return null;
    const item = apps.app_list[index];
    if (!item) return null;
    return (
      <div key={key} style={style}>
        <BlurredCard
          key={item.app_code}
          name={item.app_name}
          description={item.app_describe}
          className='w-11/12'
          RightTop={
            item.is_collected === 'true' ? (
              <StarFilled
                onClick={() => collect(item)}
                style={{
                  height: '21px',
                  cursor: 'pointer',
                  color: '#f9c533',
                }}
              />
            ) : (
              <StarOutlined
                onClick={() => collect(item)}
                style={{
                  height: '21px',
                  cursor: 'pointer',
                }}
              />
            )
          }
          onClick={async () => {
            // Native application jump

            if (item.team_mode === 'native_app') {
              const { chat_scene = '' } = item.team_context;
              const [, res] = await apiInterceptors(newDialogue({ chat_mode: chat_scene }));
              if (res) {
                setCurrentDialogInfo?.({
                  chat_scene: res.chat_mode,
                  app_code: item.app_code,
                });
                localStorage.setItem(
                  'cur_dialog_info',
                  JSON.stringify({
                    chat_scene: res.chat_mode,
                    app_code: item.app_code,
                  }),
                );
                router.push(`/chat?scene=${chat_scene}&id=${res.conv_uid}${model ? `&model=${model}` : ''}`);
              }
            } else {
              // Customize the application
              const [, res] = await apiInterceptors(newDialogue({ chat_mode: 'chat_agent' }));
              if (res) {
                setCurrentDialogInfo?.({
                  chat_scene: res.chat_mode,
                  app_code: item.app_code,
                });
                localStorage.setItem(
                  'cur_dialog_info',
                  JSON.stringify({
                    chat_scene: res.chat_mode,
                    app_code: item.app_code,
                  }),
                );
                setAgent?.(item.app_code);
                router.push(`/chat/?scene=chat_agent&id=${res.conv_uid}${model ? `&model=${model}` : ''}`);
              }
            }
          }}
          LeftBottom={
            <div className='flex gap-8 items-center text-[#878c93] text-sm dark:text-stone-200'>
              {item.owner_name && (
                <div className='flex gap-1 items-center'>
                  <Avatar
                    src={item?.owner_avatar_url}
                    className='bg-gradient-to-tr from-[#31afff] to-[#1677ff] cursor-pointer'
                  >
                    {item.owner_name}
                  </Avatar>
                  <span>{item.owner_name}</span>
                </div>
              )}
              {activeKey === 'recommend' ? (
                <div className='flex items-start gap-1'>
                  <IconFont type='icon-hot' className='text-lg' />
                  <span className='text-[#878c93]'>{item.hot_value}</span>
                </div>
              ) : (
                <div>{moment(item?.updated_at).fromNow() + ' ' + t('update')}</div>
              )}
            </div>
          }
          scene={item?.team_context?.chat_scene || 'chat_agent'}
        />
      </div>
    );
  };
  useEffect(() => {
    // setPageNo('1');
    setApps({
      app_list: [],
      total_count: 0,
    });
  }, [activeKey]);

  useEffect(() => {
    getAppListFn();
  }, [activeKey, getAppListFn]);

  // useEffect(() => {
  //   getAppListFn();
  // }, [getAppListFn, pageNo]);

  return (
    <div
      className='flex flex-col h-full w-full backdrop-filter backdrop-blur dark:bg-gradient-dark bg-gradient-light  p-10 pt-12 '
      id='home-container'
    >
      <ConfigProvider
        theme={{
          components: {
            Button: {
              defaultBorderColor: 'white',
            },
            Segmented: {
              itemSelectedBg: '#2867f5',
              itemSelectedColor: 'white',
            },
          },
        }}
      >
        {/* Apps list */}
        <div
          className='flex flex-col h-full mt-4 overflow-hidden relative'
          style={{
            paddingBottom: apps.total_count > 12 ? 45 : 20,
          }}
        >
          {/* <div className='flex justify-between items-center'>
            <div className='flex items-center gap-4'>
              <Segmented
                className='h-10 backdrop-filter backdrop-blur-lg bg-white bg-opacity-30 border border-white rounded-lg shadow p-1 dark:border-[#6f7f95] dark:bg-[#6f7f95] dark:bg-opacity-60'
                options={items}
                onChange={key => setActiveKey(key as any)}
                value={activeKey}
              />
              <Input
                variant='filled'
                prefix={<SearchOutlined />}
                placeholder={t('please_enter_the_keywords')}
                onChange={onSearch}
                onPressEnter={onSearch}
                allowClear
                className={cls(
                  'w-[230px] h-[40px] border-1 border-white backdrop-filter backdrop-blur-lg bg-white bg-opacity-30 dark:border-[#6f7f95] dark:bg-[#6f7f95] dark:bg-opacity-60',
                  {
                    hidden: activeKey === 'recommend',
                  },
                )}
              />
            </div>

            <div className='flex items-center gap-4'>
              <Button
                className='border-none text-white bg-button-gradient'
                icon={<PlusOutlined />}
                onClick={() => {
                  localStorage.removeItem('new_app_info');
                  router.push('/construct/app?openModal=true');
                }}
              >
                {t('create_app')}
              </Button>
            </div>
          </div> */}
          {loading && !apps.app_list.length ? (
            <Spin size='large' className='flex items-center justify-center h-full' spinning={loading} />
          ) : (
            <>
              <InfiniteLoader
                isRowLoaded={isRowLoaded}
                loadMoreRows={loadMoreRows}
                rowCount={Math.ceil(apps.total_count / columnCount)} // Total number of ROWS
              >
                {({ onRowsRendered, registerChild }) => (
                  <AutoSizer>
                    {({ width, height }) => (
                      <Grid
                        ref={registerChild}
                        onSectionRendered={({ rowStartIndex, rowStopIndex }) => {
                          // Pass ROW indices directly to InfiniteLoader
                          onRowsRendered({ startIndex: rowStartIndex, stopIndex: rowStopIndex });
                        }}
                        cellRenderer={cellRenderer}
                        columnWidth={width / columnCount}
                        columnCount={columnCount}
                        height={height}
                        rowHeight={200 /* Your height */}
                        rowCount={Math.ceil(apps.total_count / columnCount)}
                        width={width}
                      />
                    )}
                  </AutoSizer>
                )}
              </InfiniteLoader>
              {loading && apps.app_list.length && (
                <Spin className='flex items-end justify-center h-full' spinning={loading} />
              )}
            </>
          )}

          {/* <TabContent apps={apps?.app_list || []} loading={loading} refresh={refresh} /> */}
        </div>
      </ConfigProvider>
    </div>
  );
};

export default Playground;

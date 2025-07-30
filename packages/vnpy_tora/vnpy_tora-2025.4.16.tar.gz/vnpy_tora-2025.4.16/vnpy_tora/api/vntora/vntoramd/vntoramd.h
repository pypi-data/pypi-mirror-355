//ϵͳ
#ifdef WIN32
#include "pch.h"
#endif

#include "vntora.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "TORATstpXMdApi.h"


using namespace pybind11;
using namespace TORALEV1API;
using namespace std;


#define ONFRONTCONNECTED 0
#define ONFRONTDISCONNECTED 1
#define ONRSPGETCONNECTIONINFO 2
#define ONRSPUSERLOGIN 3
#define ONRSPUSERLOGOUT 4
#define ONRSPSUBMARKETDATA 5
#define ONRSPUNSUBMARKETDATA 6
#define ONRSPSUBPHMARKETDATA 7
#define ONRSPUNSUBPHMARKETDATA 8
#define ONRSPSUBSPECIALMARKETDATA 9
#define ONRSPUNSUBSPECIALMARKETDATA 10
#define ONRSPSUBSIMPLIFYMARKETDATA 11
#define ONRSPUNSUBSIMPLIFYMARKETDATA 12
#define ONRSPSUBSECURITYSTATUS 13
#define ONRSPUNSUBSECURITYSTATUS 14
#define ONRSPSUBMARKETSTATUS 15
#define ONRSPUNSUBMARKETSTATUS 16
#define ONRSPSUBIMCPARAMS 17
#define ONRSPUNSUBIMCPARAMS 18
#define ONRSPINQUIRYMARKETDATAMIRROR 19
#define ONRSPINQUIRYPHMARKETDATAMIRROR 20
#define ONRSPINQUIRYSPECIALMARKETDATAMIRROR 21
#define ONRSPSUBSPMARKETDATA 22
#define ONRSPUNSUBSPMARKETDATA 23
#define ONRSPSUBSPSIMPLIFYMARKETDATA 24
#define ONRSPUNSUBSPSIMPLIFYMARKETDATA 25
#define ONRSPSUBSPSECURITYSTATUS 26
#define ONRSPUNSUBSPSECURITYSTATUS 27
#define ONRSPSUBSPMARKETSTATUS 28
#define ONRSPUNSUBSPMARKETSTATUS 29
#define ONRSPINQUIRYSPMARKETDATAMIRROR 30
#define ONRTNMARKETDATA 31
#define ONRTNPHMARKETDATA 32
#define ONRTNSPECIALMARKETDATA 33
#define ONRTNSIMPLIFYMARKETDATA 34
#define ONRTNSECURITYSTATUS 35
#define ONRTNMARKETSTATUS 36
#define ONRTNIMCPARAMS 37
#define ONRTNSPMARKETDATA 38
#define ONRTNSPSIMPLIFYMARKETDATA 39
#define ONRTNSPSECURITYSTATUS 40
#define ONRTNSPMARKETSTATUS 41
#define ONRSPSUBRAPIDMARKETDATA 42
#define ONRSPUNSUBRAPIDMARKETDATA 43
#define ONRTNRAPIDMARKETDATA 44


///-------------------------------------------------------------------------------------
///C++ SPI�Ļص���������ʵ��
///-------------------------------------------------------------------------------------

//API�ļ̳�ʵ��
class MdApi : public CTORATstpXMdSpi
{
private:
    XMD_API_DLL_EXPORT CTORATstpXMdApi* api;      //API����
    bool active = false;                //����״̬
    thread task_thread;                    //�����߳�ָ�루��python���������ݣ�
    TaskQueue task_queue;                //�������
    bool logging = false;


public:
	MdApi()
    {
    };

    ~MdApi()
    {
        if (this->active)
        {
            this->exit();
        }
    };


    //-------------------------------------------------------------------------------------
    //API�ص�����
    //-------------------------------------------------------------------------------------

	///���ͻ����뽻�׺�̨������ͨ������ʱ����δ��¼ǰ�����÷��������á�
	virtual void OnFrontConnected();

	///���ͻ����뽻�׺�̨ͨ�����ӶϿ�ʱ���÷��������á���������������API���Զ��������ӣ��ͻ��˿ɲ�������
	///        -3 �����ѶϿ�
	///        -4 �����ʧ��
	///        -5 ����дʧ��
	///        -6 ����������
	///        -7 ����Ŵ���
	///        -8 �������������
	///        -9 ����ı���
	virtual void OnFrontDisconnected(int nReason);

	///��ȡ������ϢӦ��
	virtual void OnRspGetConnectionInfo(CTORATstpConnectionInfoField* pConnectionInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��¼Ӧ��
	virtual void OnRspUserLogin(CTORATstpRspUserLoginField* pRspUserLoginField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�ǳ�Ӧ��
	virtual void OnRspUserLogout(CTORATstpUserLogoutField* pUserLogoutField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��������Ӧ��
	virtual void OnRspSubMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶�����Ӧ��
	virtual void OnRspUnSubMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�����̺�����Ӧ��
	virtual void OnRspSubPHMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶��̺�����Ӧ��
	virtual void OnRspUnSubPHMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�����ض�����Ӧ��
	virtual void OnRspSubSpecialMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶��ض�����Ӧ��
	virtual void OnRspUnSubSpecialMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///���ļ�������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspSubSimplifyMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspUnSubSimplifyMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///���ĺ�Լ״̬Ӧ��
	virtual void OnRspSubSecurityStatus(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���Լ״̬Ӧ��
	virtual void OnRspUnSubSecurityStatus(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�����г�״̬Ӧ��
	virtual void OnRspSubMarketStatus(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///�˶��г�״̬Ӧ��
	virtual void OnRspUnSubMarketStatus(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///���Ĺ����г�����״̬Ӧ��
	virtual void OnRspSubImcParams(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///�˶������г�����״̬Ӧ��
	virtual void OnRspUnSubImcParams(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///��ѯ�������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspInquiryMarketDataMirror(CTORATstpMarketDataField* pMarketDataField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�̺��������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspInquiryPHMarketDataMirror(CTORATstpPHMarketDataField* pPHMarketDataField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ض��������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspInquirySpecialMarketDataMirror(CTORATstpSpecialMarketDataField* pMarketDataField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///������Ȩ����Ӧ��
	virtual void OnRspSubSPMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���Ȩ����Ӧ��
	virtual void OnRspUnSubSPMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///������Ȩ��������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspSubSPSimplifyMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���Ȩ��������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspUnSubSPSimplifyMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///������Ȩ��Լ״̬Ӧ��
	virtual void OnRspSubSPSecurityStatus(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���Ȩ��Լ״̬Ӧ��
	virtual void OnRspUnSubSPSecurityStatus(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///������Ȩ�г�״̬Ӧ��
	virtual void OnRspSubSPMarketStatus(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///�˶���Ȩ�г�״̬Ӧ��
	virtual void OnRspUnSubSPMarketStatus(CTORATstpSpecificMarketField* pSpecificMarketField, CTORATstpRspInfoField* pRspInfoField);

	///��ѯ��Ȩ�������Ӧ�𣨽�TCPģʽ�¿��ã�
	virtual void OnRspInquirySPMarketDataMirror(CTORATstpMarketDataField* pMarketDataField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///����֪ͨ
	virtual void OnRtnMarketData(CTORATstpMarketDataField* pMarketDataField);

	///�̺�����֪ͨ
	virtual void OnRtnPHMarketData(CTORATstpPHMarketDataField* pPHMarketDataField);

	///�ض�����֪ͨ
	virtual void OnRtnSpecialMarketData(CTORATstpSpecialMarketDataField* pSpecialMarketDataField);

	///��������֪ͨ����TCPģʽ�¿��ã�
	virtual void OnRtnSimplifyMarketData(CTORATstpSimplifyMarketDataField* pSimplifyMarketDataField);

	///��Լ״̬
	virtual void OnRtnSecurityStatus(CTORATstpSecurityStatusField* pSecurityStatusField);

	///�г�״̬
	virtual void OnRtnMarketStatus(CTORATstpMarketStatusField* pMarketStatusField);

	///�����г�����״̬
	virtual void OnRtnImcParams(CTORATstpImcParamsField* pImcParamsField);

	///��Ȩ����֪ͨ
	virtual void OnRtnSPMarketData(CTORATstpMarketDataField* pMarketDataField);

	///��Ȩ��������֪ͨ����TCPģʽ�¿��ã�
	virtual void OnRtnSPSimplifyMarketData(CTORATstpSimplifyMarketDataField* pSimplifyMarketDataField);

	///��Ȩ��Լ״̬֪ͨ
	virtual void OnRtnSPSecurityStatus(CTORATstpSecurityStatusField* pSecurityStatusField);

	///��Ȩ�г�״̬֪ͨ
	virtual void OnRtnSPMarketStatus(CTORATstpMarketStatusField* pMarketStatusField);


	///���ĺϳɿ���Ӧ����������
	virtual void OnRspSubRapidMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�˶��ϳɿ���Ӧ����������
	virtual void OnRspUnSubRapidMarketData(CTORATstpSpecificSecurityField* pSpecificSecurityField, CTORATstpRspInfoField* pRspInfoField);

	///�ϳɿ���֪ͨ����������
	virtual void OnRtnRapidMarketData(CTORATstpRapidMarketDataField* pRapidMarketDataField);

	//-------------------------------------------------------------------------------------
	//data���ص������������ֵ�
	//-------------------------------------------------------------------------------------

	virtual void onFrontConnected() {};

	virtual void onFrontDisconnected(int nReason) {};

	virtual void onRspGetConnectionInfo(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspUserLogin(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspUserLogout(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspSubMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubPHMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubPHMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubSpecialMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubSpecialMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubSimplifyMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubSimplifyMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubSecurityStatus(const dict& data, const dict& error) {};

	virtual void onRspUnSubSecurityStatus(const dict& data, const dict& error) {};

	virtual void onRspSubMarketStatus(const dict& data, const dict& error) {};

	virtual void onRspUnSubMarketStatus(const dict& data, const dict& error) {};

	virtual void onRspSubImcParams(const dict& data, const dict& error) {};

	virtual void onRspUnSubImcParams(const dict& data, const dict& error) {};

	virtual void onRspInquiryMarketDataMirror(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspInquiryPHMarketDataMirror(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspInquirySpecialMarketDataMirror(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspSubSPMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubSPMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubSPSimplifyMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubSPSimplifyMarketData(const dict& data, const dict& error) {};

	virtual void onRspSubSPSecurityStatus(const dict& data, const dict& error) {};

	virtual void onRspUnSubSPSecurityStatus(const dict& data, const dict& error) {};

	virtual void onRspSubSPMarketStatus(const dict& data, const dict& error) {};

	virtual void onRspUnSubSPMarketStatus(const dict& data, const dict& error) {};

	virtual void onRspInquirySPMarketDataMirror(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRtnMarketData(const dict& data) {};

	virtual void onRtnPHMarketData(const dict& data) {};

	virtual void onRtnSpecialMarketData(const dict& data) {};

	virtual void onRtnSimplifyMarketData(const dict& data) {};

	virtual void onRtnSecurityStatus(const dict& data) {};

	virtual void onRtnMarketStatus(const dict& data) {};

	virtual void onRtnImcParams(const dict& data) {};

	virtual void onRtnSPMarketData(const dict& data) {};

	virtual void onRtnSPSimplifyMarketData(const dict& data) {};

	virtual void onRtnSPSecurityStatus(const dict& data) {};

	virtual void onRtnSPMarketStatus(const dict& data) {};

	virtual void onRspSubRapidMarketData(const dict& data, const dict& error) {};

	virtual void onRspUnSubRapidMarketData(const dict& data, const dict& error) {};

	virtual void onRtnRapidMarketData(const dict& data) {};

	//-------------------------------------------------------------------------------------
	//task������
	//-------------------------------------------------------------------------------------

	void processTask();

	void processFrontConnected(Task* task);

	void processFrontDisconnected(Task* task);

	void processRspGetConnectionInfo(Task* task);

	void processRspUserLogin(Task* task);

	void processRspUserLogout(Task* task);

	void processRspSubMarketData(Task* task);

	void processRspUnSubMarketData(Task* task);

	void processRspSubPHMarketData(Task* task);

	void processRspUnSubPHMarketData(Task* task);

	void processRspSubSpecialMarketData(Task* task);

	void processRspUnSubSpecialMarketData(Task* task);

	void processRspSubSimplifyMarketData(Task* task);

	void processRspUnSubSimplifyMarketData(Task* task);

	void processRspSubSecurityStatus(Task* task);

	void processRspUnSubSecurityStatus(Task* task);

	void processRspSubMarketStatus(Task* task);

	void processRspUnSubMarketStatus(Task* task);

	void processRspSubImcParams(Task* task);

	void processRspUnSubImcParams(Task* task);

	void processRspInquiryMarketDataMirror(Task* task);

	void processRspInquiryPHMarketDataMirror(Task* task);

	void processRspInquirySpecialMarketDataMirror(Task* task);

	void processRspSubSPMarketData(Task* task);

	void processRspUnSubSPMarketData(Task* task);

	void processRspSubSPSimplifyMarketData(Task* task);

	void processRspUnSubSPSimplifyMarketData(Task* task);

	void processRspSubSPSecurityStatus(Task* task);

	void processRspUnSubSPSecurityStatus(Task* task);

	void processRspSubSPMarketStatus(Task* task);

	void processRspUnSubSPMarketStatus(Task* task);

	void processRspInquirySPMarketDataMirror(Task* task);

	void processRtnMarketData(Task* task);

	void processRtnPHMarketData(Task* task);

	void processRtnSpecialMarketData(Task* task);

	void processRtnSimplifyMarketData(Task* task);

	void processRtnSecurityStatus(Task* task);

	void processRtnMarketStatus(Task* task);

	void processRtnImcParams(Task* task);

	void processRtnSPMarketData(Task* task);

	void processRtnSPSimplifyMarketData(Task* task);

	void processRtnSPSecurityStatus(Task* task);

	void processRtnSPMarketStatus(Task* task);

	void processRspSubRapidMarketData(Task* task);

	void processRspUnSubRapidMarketData(Task* task);

	void processRtnRapidMarketData(Task* task);

	//-------------------------------------------------------------------------------------
	//req:���������������ֵ�
	//-------------------------------------------------------------------------------------

	void createTstpXMdApi();

	void registerFront(string pszFrontAddress);

	void init();

	int join();

	void release();

	string getApiVersion();

	int exit();

	void registerNameServer(string pszNsAddress);

	void registerFensUserInfo(const dict& req);

	void registerMulticast(string pszMulticastAddress, string pszInterfaceIP, string pszSourceIp);

	void registerDeriveServer(string pszDeriveAddress);

	void registerDeriveMulticast(string pszMulticastAddress, string pszInterfaceIP, string pszSourceIp);

	int reqGetConnectionInfo(int nrequestid);

	int reqUserLogin(const dict& req, int nrequestid);

	int reqUserLogout(const dict& req, int nrequestid);

	int subscribeMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribePHMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribePHMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSpecialMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSpecialMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSimplifyMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSimplifyMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSecurityStatus(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSecurityStatus(string ppsecurityid, int ncount, string exchangeid);

	int subscribeMarketStatus(string marketid);

	int unSubscribeMarketStatus(string marketid);

	int subscribeImcParams(string marketid);

	int unSubscribeImcParams(string marketid);

	int reqInquiryMarketDataMirror(const dict& req, int nrequestid);

	int reqInquiryPHMarketDataMirror(const dict& req, int nrequestid);

	int reqInquirySpecialMarketDataMirror(const dict& req, int nrequestid);

	int subscribeSPMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSPMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSPSimplifyMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSPSimplifyMarketData(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSPSecurityStatus(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeSPSecurityStatus(string ppsecurityid, int ncount, string exchangeid);

	int subscribeSPMarketStatus(string marketid);

	int unSubscribeSPMarketStatus(string marketid);

	int reqInquirySPMarketDataMirror(const dict& req, int nrequestid);

	int subscribeRapidMarketData(string ppsecurityid, int ncount, string exchangeid);

	int unSubscribeRapidMarketData(string ppsecurityid, int ncount, string exchangeid);
};

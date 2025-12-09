/**
 * Stub data generator for testing when real APIs are not available
 */

interface StubDataOptions {
  source: string;
  filters: any;
  count?: number;
}

export class StubDataGenerator {
  static generate(options: StubDataOptions): any[] {
    const { source, filters, count = 50 } = options;

    switch (source) {
      case 'rone':
        return this.generateRealEstateData(filters, count);
      case 'nec_manifesto':
        return this.generateElectionData(filters, count);
      case 'nabostats':
        return this.generateFinanceData(filters, count);
      case 'youtube':
        return this.generateYoutubeData(filters, count);
      default:
        return this.generateGenericData(filters, count);
    }
  }

  private static generateRealEstateData(filters: any, count: number): any[] {
    const data: any[] = [];
    const region = filters.region || '강남구';
    const startDate = filters.dateRange?.start
      ? new Date(filters.dateRange.start)
      : new Date('2015-01-01');
    const endDate = filters.dateRange?.end ? new Date(filters.dateRange.end) : new Date();

    // Generate monthly data points
    const monthsDiff = this.getMonthDifference(startDate, endDate);
    const actualCount = Math.min(count, monthsDiff + 1);

    let basePrice = 800000000; // 8억 기준
    const trend = 1.005; // 월 0.5% 상승 트렌드

    for (let i = 0; i < actualCount; i++) {
      const date = new Date(startDate);
      date.setMonth(date.getMonth() + i);

      // Add some randomness
      const randomFactor = 0.95 + Math.random() * 0.1;
      const price = Math.floor(basePrice * Math.pow(trend, i) * randomFactor);

      data.push({
        date: date.toISOString().split('T')[0],
        region,
        averagePrice: price,
        tradingVolume: Math.floor(100 + Math.random() * 200),
        priceChangeRate:
          i > 0
            ? (((price - data[i - 1].averagePrice) / data[i - 1].averagePrice) * 100).toFixed(2)
            : '0.00',
      });
    }

    return data;
  }

  private static generateElectionData(filters: any, count: number): any[] {
    const data: any[] = [];
    const year = filters.election?.year || 2022;
    const region = filters.region || '서울';

    const parties = ['더불어민주당', '국민의힘', '정의당', '무소속'];
    const positions = ['시장', '도지사', '구청장', '시의원'];

    for (let i = 0; i < count; i++) {
      data.push({
        year,
        region: `${region} ${i + 1}선거구`,
        candidateName: `후보${i + 1}`,
        party: parties[i % parties.length],
        position: positions[i % positions.length],
        votes: Math.floor(10000 + Math.random() * 50000),
        voteRate: (Math.random() * 40 + 10).toFixed(2) + '%',
        isElected: i % 5 === 0,
        pledges: ['교통 인프라 확충', '교육 환경 개선', '복지 정책 강화'],
      });
    }

    return data;
  }

  private static generateFinanceData(filters: any, count: number): any[] {
    const data: any[] = [];
    const year = filters.dateRange?.start ? new Date(filters.dateRange.start).getFullYear() : 2024;

    const categories = ['세입', '세출', '지방채', '교부금'];
    const regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산'];

    for (let i = 0; i < count; i++) {
      data.push({
        year: year - Math.floor(i / 10),
        quarter: (i % 4) + 1,
        region: regions[i % regions.length],
        category: categories[i % categories.length],
        amount: Math.floor(1000000000 + Math.random() * 5000000000),
        growthRate: (Math.random() * 20 - 5).toFixed(2) + '%',
      });
    }

    return data;
  }

  private static generateYoutubeData(filters: any, count: number): any[] {
    const data: any[] = [];
    const keywords = filters.keywords || ['정책', '공약'];

    const channels = ['KBS뉴스', 'JTBC뉴스', 'MBC뉴스', 'SBS뉴스', 'YTN'];

    for (let i = 0; i < count; i++) {
      data.push({
        videoId: `VIDEO${i.toString().padStart(8, '0')}`,
        title: `${keywords[0]} 관련 뉴스 ${i + 1}`,
        channel: channels[i % channels.length],
        publishedAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
        views: Math.floor(1000 + Math.random() * 100000),
        likes: Math.floor(10 + Math.random() * 1000),
        duration: `${Math.floor(Math.random() * 30 + 1)}:${Math.floor(Math.random() * 60)
          .toString()
          .padStart(2, '0')}`,
      });
    }

    return data;
  }

  private static generateGenericData(filters: any, count: number): any[] {
    const data: any[] = [];

    for (let i = 0; i < count; i++) {
      data.push({
        id: i + 1,
        name: `데이터 ${i + 1}`,
        category: `카테고리 ${(i % 5) + 1}`,
        value: Math.floor(Math.random() * 1000),
        timestamp: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
      });
    }

    return data;
  }

  private static getMonthDifference(startDate: Date, endDate: Date): number {
    return (
      (endDate.getFullYear() - startDate.getFullYear()) * 12 +
      (endDate.getMonth() - startDate.getMonth())
    );
  }
}

require 'json'

module Jekyll
  class TrailPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      trails = load_json(site, '_rawdata/trails.json')
      return if trails.empty?

      Jekyll.logger.info "TrailGenerator:", "#{trails.size}개 길 페이지 생성 중..."

      trails.each do |trail|
        next if trail['slug'].to_s.strip.empty?
        site.pages << TrailPage.new(site, trail)
      end

      by_region = trails.group_by { |t| t['doNm'] }
      by_region.each do |do_nm, do_trails|
        next if do_nm.to_s.strip.empty?
        site.pages << RegionPage.new(site, do_nm, do_trails)
      end

      site.pages << SearchIndexPage.new(site, trails)

      Jekyll.logger.info "TrailGenerator:", "완료 (#{trails.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "TrailGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class TrailPage < Page
    def initialize(site, trail)
      @site = site
      @base = site.source
      @dir  = "trail/#{trail['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'trail.html')
      trail_data = trail.dup
      trail_data['trailName'] = trail_data.delete('name')
      self.data.merge!(trail_data)
      self.data['layout']      = 'trail'
      self.data['title']       = build_title(trail)
      self.data['description'] = build_desc(trail)
    end

    private

    def build_title(t)
      loc = [t['doNm'], t['sigunguNm']].compact.join(' ')
      "#{t['name']} #{loc} 거리 소요시간"
    end

    def build_desc(t)
      loc = [t['doNm'], t['sigunguNm']].compact.join(' ')
      d = "#{loc} #{t['name']}. 총거리 #{t['distanceKm']}km, 소요시간 #{t['duration']}."
      d += " #{t['intro']}" if t['intro'].to_s.length > 3
      d[0, 155]
    end
  end

  class RegionPage < Page
    def initialize(site, do_nm, trails)
      @site = site
      @base = site.source
      @dir  = "region/#{do_nm}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'region.html')
      self.data['layout']  = 'region'
      self.data['doNm']    = do_nm
      self.data['trails']  = trails
      self.data['title']       = "#{do_nm} 둘레길·트레킹길 정보"
      self.data['description'] = "#{do_nm} 둘레길·트레킹길 #{trails.size}개 목록. 거리, 소요시간, 시작·종료 지점을 확인하세요."
    end
  end

  class SearchIndexPage < Page
    def initialize(site, trails)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = trails.map do |t|
        {
          'slug'        => t['slug'],
          'name'        => t['name'],
          'doNm'        => t['doNm'],
          'sigunguNm'   => t['sigunguNm'],
          'distanceKm'  => t['distanceKm'],
          'duration'    => t['duration'],
          'intro'       => (t['intro'] || '')[0, 80],
        }
      end

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end

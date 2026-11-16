export type Who = { gamertag: string; displayName: string };
export type Result = "win" | "draw" | "loss";
export type Archetype = { id: number; name: string };

export type Match = {
  matchId: string;
  timestamp: string;
  opponentName: string;
  opponentCrestUrl: string;
  goals: number;
  goalsAgainst: number;
  result: Result;
  dnf: boolean;
  motm: Who | null;
  best: (Who & { rating: number }) | null;
};

export type Player = Who & {
  position: string;
  overall: number;
  gamesPlayed: number;
  winRate: number;
  goals: number;
  assists: number;
  averageRating: number;
  manOfTheMatch: number;
  shotSuccessRate: number;
  passesMade: number;
  passSuccessRate: number;
  tacklesMade: number;
  tackleSuccessRate: number;
  cleanSheetsDef: number;
  cleanSheetsGK: number;
  redCards: number;
  /** Archetype used in the player's most recent saved match. */
  archetype: Archetype | null;
};

export type MatchPlayer = Who & {
  position: string;
  rating: number;
  goals: number;
  assists: number;
  shots: number;
  passesMade: number;
  passAttempts: number;
  tacklesMade: number;
  tackleAttempts: number;
  saves: number;
  manOfTheMatch: boolean;
  secondsPlayed: number;
  archetype: Archetype | null;
};

export type Leader = (Who & { value: number }) | null;

export type Overview = {
  club: {
    clubId: number;
    name: string;
    crestUrl: string;
    stadium: string;
    division: number;
    bestDivision: number;
    promotions: number;
    relegations: number;
    skillRating: number;
  };
  season: { gamesPlayed: number; wins: number; ties: number; losses: number; points: number; goals: number; goalsAgainst: number };
  allTime: {
    gamesPlayed: number;
    wins: number;
    ties: number;
    losses: number;
    goals: number;
    goalsAgainst: number;
    winStreak: number;
    unbeatenStreak: number;
  };
  recentMatches: Match[];
  mvpCounts: (Who & { count: number })[];
  leaders: { goals: Leader; assists: Leader; rating: Leader };
  players: Player[];
  updatedAt: string;
};

export type Status = { lastAttemptAt: string | null; lastSuccessAt: string | null; lastError: string | null };

export type PlayerDetail = {
  player: Player;
  history: {
    matchId: string;
    timestamp: string;
    rating: number;
    goals: number;
    assists: number;
    motm: boolean;
    result: Result;
    archetype: Archetype | null;
  }[];
  tracked: { games: number; goals: number; assists: number; motm: number; avgRating: number };
  archetypes: ArchetypeSplit[];
};

export type ArchetypeSplit = Archetype & {
  games: number;
  wins: number;
  draws: number;
  losses: number;
  goals: number;
  assists: number;
  motm: number;
  avgRating: number | null;
  lastPlayed: string;
};

export type Session = { start: string; wins: number; draws: number; losses: number; matches: Match[] };
export type MatchesResponse = { sessions: Session[]; nextBefore: string | null };
export type MatchDetail = { match: Match; players: MatchPlayer[] };

export type Outcome = "promoted" | "relegated" | "stayed" | "in_progress";
export type Campaign = {
  division: number;
  startedAt: string;
  endedAt: string | null;
  outcome: Outcome;
  partial: boolean;
  wins: number;
  draws: number;
  losses: number;
  goals: number;
  goalsAgainst: number;
  topScorer: Leader;
  topMvp: Leader;
};
export type EASeason = {
  startedAt: string;
  endedAt: string | null;
  partial: boolean;
  promotionsBeforeTracking: number;
  totals: {
    gamesPlayed: number;
    wins: number;
    ties: number;
    losses: number;
    points: number;
    goals: number;
    goalsAgainst: number;
    promotions: number;
    relegations: number;
  };
  campaigns: Campaign[];
};
export type SeasonsResponse = { eaSeasons: EASeason[] };

export type TimeSlot = {
  slot: "morning" | "afternoon" | "night";
  label: string;
  startHour: number;
  endHour: number;
  games: number;
  wins: number;
  draws: number;
  losses: number;
  winRate: number;
};
export type TimeOfDayResponse = { slots: TimeSlot[] };

export type Opponent = {
  opponentId: number | null;
  name: string;
  crestUrl: string;
  games: number;
  wins: number;
  draws: number;
  losses: number;
  goals: number;
  goalsAgainst: number;
  lastPlayed: string;
  matches: Match[];
};

export type ArchetypeRecord = Archetype & {
  /** Matches where at least one of our players used this archetype. */
  games: number;
  wins: number;
  draws: number;
  losses: number;
  winRate: number;
  playerGames: number;
  goals: number;
  assists: number;
  motm: number;
  avgRating: number | null;
  /** Each of our players' numbers in this archetype. */
  players: (Who & Omit<ArchetypeSplit, keyof Archetype>)[];
};
export type ArchetypesResponse = { archetypes: ArchetypeRecord[]; unused: string[] };
